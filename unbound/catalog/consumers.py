import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.db.models import Q


class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.user = self.scope['user']
        self.other_id = int(self.scope['url_route']['kwargs']['other_id'])

        if not self.user.is_authenticated:
            await self.close()
            return

        is_admin = await self._is_admin()
        if not is_admin:
            is_friend = await self._check_friendship()
            if not is_friend:
                await self.close()
                return

        ids = sorted([self.user.pk, self.other_id])
        self.room_group = f'chat_{ids[0]}_{ids[1]}'

        await self.channel_layer.group_add(self.room_group, self.channel_name)
        await self.accept()

        # Помечаем входящие сообщения как прочитанные при открытии диалога
        await self._mark_read()

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group'):
            await self.channel_layer.group_discard(self.room_group, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        if data.get('type') == 'ping':
            await self.send(text_data=json.dumps({'type': 'pong'}))
            return
        text = data.get('text', '').strip()
        if not text:
            return

        msg = await self._save_message(text)
        await self._create_notification()

        await self.channel_layer.group_send(
            self.room_group,
            {
                'type': 'chat_message',
                'msg_id':    msg['id'],
                'text':      msg['text'],
                'sender_id': self.user.pk,
                'time':      msg['time'],
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'msg_id':    event['msg_id'],
            'text':      event['text'],
            'sender_id': event['sender_id'],
            'time':      event['time'],
        }))

    # ── DB helpers ────────────────────────────────────────────────────────────

    @database_sync_to_async
    def _is_admin(self):
        return self.user.is_admin()

    @database_sync_to_async
    def _check_friendship(self):
        from .models import Friendship
        return Friendship.objects.filter(
            Q(from_user=self.user, to_user_id=self.other_id, status='accepted') |
            Q(from_user_id=self.other_id, to_user=self.user, status='accepted')
        ).exists()

    @database_sync_to_async
    def _save_message(self, text):
        from .models import Conversation, Message
        conv = (
            Conversation.objects
            .filter(participants=self.user)
            .filter(participants__pk=self.other_id)
            .first()
        )
        if not conv:
            conv = Conversation.objects.create()
            conv.participants.add(self.user.pk, self.other_id)

        msg = Message.objects.create(conversation=conv, sender=self.user, text=text)
        conv.save()
        return {
            'id':   msg.pk,
            'text': msg.text,
            'time': msg.created_at.strftime('%d.%m %H:%M'),
        }

    @database_sync_to_async
    def _mark_read(self):
        from .models import Conversation, Message
        conv = (
            Conversation.objects
            .filter(participants=self.user)
            .filter(participants__pk=self.other_id)
            .first()
        )
        if conv:
            conv.messages.filter(is_read=False).exclude(sender=self.user).update(is_read=True)

    @database_sync_to_async
    def _create_notification(self):
        from .models import User, Notification
        try:
            other = User.objects.get(pk=self.other_id)
            Notification.create(
                recipient=other,
                ntype='message',
                text=f'{self.user.username} написал вам сообщение',
                link=f'/messages/{self.user.pk}/',
            )
        except User.DoesNotExist:
            pass


class ForumConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.user = self.scope['user']
        if not self.user.is_authenticated:
            await self.close()
            return
        self.thread_id = int(self.scope['url_route']['kwargs']['thread_id'])
        self.room_group = f'forum_thread_{self.thread_id}'
        await self.channel_layer.group_add(self.room_group, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group'):
            await self.channel_layer.group_discard(self.room_group, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        if data.get('type') == 'ping':
            await self.send(text_data=json.dumps({'type': 'pong'}))
            return
        text = data.get('text', '').strip()
        if not text:
            return
        post = await self._save_post(text)
        if post is None:
            return
        await self.channel_layer.group_send(self.room_group, {
            'type':       'forum_post',
            'pk':         post['pk'],
            'text':       post['text'],
            'created_at': post['created_at'],
            'author':     post['author'],
            'author_pk':  post['author_pk'],
            'avatar':     post['avatar'],
            'post_count': post['post_count'],
        })

    async def forum_post(self, event):
        await self.send(text_data=json.dumps(event))

    @database_sync_to_async
    def _save_post(self, text):
        from .models import ForumThread, ForumPost, Notification
        try:
            thread = ForumThread.objects.get(pk=self.thread_id)
        except ForumThread.DoesNotExist:
            return None
        if thread.is_closed and not self.user.is_admin():
            return None
        post = ForumPost.objects.create(thread=thread, author=self.user, text=text)
        thread.save()
        if thread.author != self.user:
            Notification.create(
                recipient=thread.author,
                ntype='forum_reply',
                text=f'{self.user.username} ответил в теме «{thread.title[:50]}»',
                link=f'/forum/thread/{thread.pk}/',
            )
        avatar_url = self.user.avatar.url if self.user.avatar else None
        return {
            'pk':         post.pk,
            'text':       post.text,
            'created_at': post.created_at.strftime('%d.%m.%Y %H:%M'),
            'author':     self.user.username,
            'author_pk':  self.user.pk,
            'avatar':     avatar_url,
            'post_count': self.user.forum_posts.count(),
        }
