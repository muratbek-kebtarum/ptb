from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, CallbackContext, filters
from db import create_table, add_data, get_data, update_data, delete_data

# Создание таблицы в БД при запуске
create_table()


# Команда /start
async def start(update: Update):
    print("Вызвана команда /start")
    keyboard = [
        [InlineKeyboardButton("Добавить задачу", callback_data='add')],
        [InlineKeyboardButton("Посмотреть задачи", callback_data='list')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Привет! Выберите действие:", reply_markup=reply_markup)


# Команда для добавления задачи
async def add(update: Update, context: CallbackContext):
    print("Вызвана команда /add")
    user_id = update.effective_user.id
    data = context.user_data.get('task_data')

    if not data:
        await update.message.reply_text("Пожалуйста, укажите задачу для добавления с помощью ввода текста.")
        return

    try:
        add_data(user_id, data)
        await update.message.reply_text("Задача успешно добавлена!")
        del context.user_data['task_data']  # Очистка сохраненных данных
    except Exception as e:
        print(f"Ошибка при добавлении задачи: {e}")
        await update.message.reply_text("Произошла ошибка при добавлении задачи. Попробуйте снова.")


# Команда для отображения списка задач
async def list_data(update: Update, context: CallbackContext):
    print("Вызвана команда /list")
    user_id = update.effective_user.id
    try:
        records = get_data(user_id)
        if not records:
            await update.message.reply_text("У вас нет задач.")
            return

        keyboard = []
        for record in records:
            keyboard.append(
                [InlineKeyboardButton(f"Обновить: {record['data']}", callback_data=f'update_{record["id"]}'),
                 InlineKeyboardButton(f"Удалить: {record['data']}", callback_data=f'delete_{record["id"]}')])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Выберите задачу для обновления или удаления:", reply_markup=reply_markup)
    except Exception as e:
        print(f"Ошибка при получении списка задач: {e}")
        await update.message.reply_text("Произошла ошибка при получении списка задач.")


# Обработчик для обновления задачи
async def update(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    action = query.data
    if action.startswith('update_'):
        try:
            record_id = int(action.split('_')[1])
            user_id = update.effective_user.id
            record = get_data(user_id, record_id)
            if record:
                await query.edit_message_text(f"Задача для обновления: {record['data']}\nВведите новые данные:")
                context.user_data['update_record_id'] = record_id
            else:
                await query.edit_message_text("Задача не найдена.")
        except Exception as e:
            print(f"Ошибка при обновлении задачи: {e}")
            await query.edit_message_text("Произошла ошибка. Попробуйте снова.")


# Обработчик для удаления задачи
async def delete(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    action = query.data
    if action.startswith('delete_'):
        try:
            record_id = int(action.split('_')[1])
            user_id = update.effective_user.id
            record = get_data(user_id, record_id)
            if record:
                keyboard = [
                    [InlineKeyboardButton("Да, удалить", callback_data=f'confirm_delete_{record_id}')],
                    [InlineKeyboardButton("Нет, отменить", callback_data='cancel_delete')],
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(f"Вы уверены, что хотите удалить задачу: {record['data']}?",
                                              reply_markup=reply_markup)
            else:
                await query.edit_message_text("Задача не найдена.")
        except Exception as e:
            print(f"Ошибка при удалении задачи: {e}")
            await query.edit_message_text("Произошла ошибка. Попробуйте снова.")


# Подтверждение удаления
async def confirm_delete(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    action = query.data
    if action.startswith('confirm_delete_'):
        try:
            record_id = int(action.split('_')[2])
            user_id = update.effective_user.id
            delete_data(user_id, record_id)
            await query.edit_message_text("Задача успешно удалена!")
        except Exception as e:
            print(f"Ошибка при подтверждении удаления: {e}")
            await query.edit_message_text("Произошла ошибка. Попробуйте снова.")
    elif action == 'cancel_delete':
        await query.edit_message_text("Удаление отменено.")


# Обработка ввода нового описания задачи
async def handle_update_input(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    new_data = update.message.text

    # Проверяем, есть ли идентификатор задачи для обновления в контексте
    if 'update_record_id' in context.user_data:
        try:
            record_id = context.user_data['update_record_id']
            update_data(user_id, record_id, new_data)
            await update.message.reply_text("Задача успешно обновлена!")
            del context.user_data['update_record_id']  # Очищаем контекст
        except Exception as e:
            print(f"Ошибка при обновлении задачи: {e}")
            await update.message.reply_text("Произошла ошибка при обновлении задачи.")
    else:
        await update.message.reply_text("Невозможно обновить задачу, попробуйте снова.")

async def cancel_delete(update: Update, context: CallbackContext):
    """Обработчик для отмены удаления."""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Удаление отменено.")

async def handle_input(update: Update, context: CallbackContext):
    # Если задача уже на стадии обновления, переходим к обновлению
    if 'update_record_id' in context.user_data:
        await handle_update_input(update, context)
        return

    context.user_data['task_data'] = update.message.text
    await update.message.reply_text("Теперь используйте команду /add для добавления задачи.")

# Основная функция
def main():
    TOKEN = "TOKEN"


    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("add", add))
    application.add_handler(CommandHandler("list", list_data))
    application.add_handler(CallbackQueryHandler(update, pattern='^update_'))
    application.add_handler(CallbackQueryHandler(delete, pattern='^delete_'))
    application.add_handler(CallbackQueryHandler(confirm_delete, pattern='^confirm_delete_'))
    # application.add_handler(CallbackQueryHandler(lambda update, context: None, pattern='^cancel_delete$'))
    application.add_handler(CallbackQueryHandler(cancel_delete, pattern='^cancel_delete$'))
    # Обработчик для ввода нового описания задачи
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_input))
    # Обработчик для изменения описания задачи
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_update_input))

    application.run_polling()

if __name__ == "__main__":
    main()




