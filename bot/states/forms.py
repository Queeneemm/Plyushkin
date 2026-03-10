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
    waiting_edit_name = State()
    waiting_edit_aliases = State()


class AccessStates(StatesGroup):
    waiting_user_identifier = State()
    waiting_user_role = State()


class EditItemStates(StatesGroup):
    waiting_new_quantity = State()
