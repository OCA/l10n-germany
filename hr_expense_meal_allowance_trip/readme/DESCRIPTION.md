This module bridges `hr_expense_meal_allowance` and `hr_expense_trip`.

It adds a **Create Meal Allowance** button to the trip form. The button is only
shown when the trip's employee belongs to a German company (company country set
to Germany), since German "Verpflegungsmehraufwände" only apply there.

Clicking the button opens a new meal allowance expense pre-filled with the trip's
employee, travel dates and linked to the trip, so the daily meal allowance lines
are calculated automatically.

The link also works from the expense side:

- Selecting a trip on a meal allowance fills the employee, travel begin, travel
  end and customer from the trip if they are still empty. Values that were
  entered before the trip was selected are kept.
- Creating a new trip from the trip field of a meal allowance pre-fills the trip
  with the employee, description, customer and travel dates of the expense.

The module is marked as `auto_install`, so it is installed automatically as soon
as both `hr_expense_meal_allowance` and `hr_expense_trip` are installed.
