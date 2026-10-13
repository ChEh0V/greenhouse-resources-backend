-- Активные сессии пользователей (лекция 6, слайд 10).
-- Для каждого ключа session:<ид> выводит пользователя и оставшееся время жизни.
-- Запуск: docker exec greenhouse_redis redis-cli --eval /scripts/active_sessions.lua
local result = {}
for _, key in ipairs(redis.call('KEYS', 'session:*')) do
    table.insert(result, key .. ' -> ' .. redis.call('GET', key)
        .. ' (TTL ' .. redis.call('TTL', key) .. ' c)')
end
return result
