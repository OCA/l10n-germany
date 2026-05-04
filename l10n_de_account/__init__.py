from . import models
from . import wizards


def _l10n_de_account_post_init(env):
    lang = env["res.lang"]
    if lang._lang_get("de_DE"):
        lang.update_menu_finance_de_translation()
