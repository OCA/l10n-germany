This module bridges `hr_expense_meal_allowance` and `hr_expense_trip`.

It adds a **Create Meal Allowance** button to the trip form. The button is only
shown when the trip's employee belongs to a German company (company country set
to Germany), since German "Verpflegungsmehraufwände" only apply there.

Clicking the button opens a new meal allowance expense pre-filled with the trip's
employee, travel dates and linked to the trip, so the daily meal allowance lines
are calculated automatically.

The module is marked as `auto_install`, so it is installed automatically as soon
as both `hr_expense_meal_allowance` and `hr_expense_trip` are installed.
