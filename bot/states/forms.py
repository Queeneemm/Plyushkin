from aiogram.fsm.state import State, StatesGroup


class InventoryStates(StatesGroup):
    waiting_search_query = State()
    waiting_quantity = State()
    waiting_duplicate_action = State()
    waiting_finish_crm_file = State()


class PoolStates(StatesGroup):
    waiting_import_file = State()
    waiting_manual_name = State()
    waiting_manual_aliases = State()
    waiting_search_query = State()
    waiting_archive_id = State()
    waiting_restore_id = State()
    waiting_rename_id = State()
    waiting_rename_name = State()
    waiting_aliases_id = State()
    waiting_aliases_value = State()


class AccessStates(StatesGroup):
    waiting_user_identifier = State()
    waiting_user_role = State()
    waiting_revoke_identifier = State()


class SummaryStates(StatesGroup):
    waiting_chat_choice = State()


class EditItemStates(StatesGroup):
    waiting_new_quantity = State()
