from channels.generic.websocket import AsyncJsonWebsocketConsumer

class UnreadConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        user = self.scope.get('user')
        if not user or not getattr(user, 'is_authenticated', False):
            # reject unauthorized
            await self.close()
            return

        self.user = user
        self.group_name = f'user_{user.id}'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        try:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
        except Exception:
            pass

    async def unread_count(self, event):
        # event contains 'unread'
        await self.send_json({
            'type': 'unread_count',
            'unread': event.get('unread', 0)
        })

    async def receive_json(self, content, **kwargs):
        # no-op: this consumer is server push only
        return
