# ban_manager.py
from connect import UserBan, AdminActionLog
import datetime

class BanManager:
    def ban_user(self, username, banned_by, reason=""):
        try:
            # Проверяем, не забанен ли уже пользователь
            ban, created = UserBan.get_or_create(
                username=username,
                defaults={
                    'banned_by': banned_by,
                    'ban_reason': reason,
                    'is_active': True
                }
            )
            if not created:
                # Если уже есть запись, обновляем ее
                ban.banned_by = banned_by
                ban.ban_reason = reason
                ban.is_active = True
                ban.ban_date = datetime.datetime.now()
                ban.save()

            # Логируем действие
            AdminActionLog.create(
                admin_username=banned_by,
                action_type='ban',
                target_username=username,
                details=f"Причина: {reason}"
            )
            return True, "Пользователь забанен"
        except Exception as e:
            return False, str(e)

    def unban_user(self, username, unbanned_by):
        try:
            ban = UserBan.get(UserBan.username == username, UserBan.is_active == True)
            ban.is_active = False
            ban.save()

            AdminActionLog.create(
                admin_username=unbanned_by,
                action_type='unban',
                target_username=username,
                details="Разбан"
            )
            return True, "Пользователь разбанен"
        except UserBan.DoesNotExist:
            return False, "Пользователь не найден или не забанен"
        except Exception as e:
            return False, str(e)

    def is_banned(self, username):
        try:
            ban = UserBan.get(UserBan.username == username, UserBan.is_active == True)
            return True
        except UserBan.DoesNotExist:
            return False

    def get_banned_users(self):
        query = UserBan.select().where(UserBan.is_active == True)
        return [ban.username for ban in query]

    def get_ban_history(self, username=None):
        query = AdminActionLog.select().where(AdminActionLog.action_type.in_(['ban', 'unban']))
        if username:
            query = query.where(AdminActionLog.target_username == username)
        return query.order_by(AdminActionLog.action_date.desc())