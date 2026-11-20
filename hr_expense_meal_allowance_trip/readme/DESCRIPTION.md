This module bridges `hr_expense_meal_allowance` and `hr_expense_trip`.

It adds a **Create Meal Allowance** button to the trip form. The button is only
shown when a meal allowance can be created for the trip:

- the trip's employee belongs to a German company (company country set to
  Germany), since German "Verpflegungsmehraufwände" only apply there, and
- the trip is not done yet.

A trip can have several meal allowances, for example one per country or rate.

Clicking the button opens a new meal allowance expense pre-filled with the trip's
employee, travel dates and customer and linked to the trip, so the daily meal
allowance lines are calculated automatically. The expensable product carrying
the *Meal Allowance* tag of the employee's company is used.

The link also works from the expense side:

- Selecting a trip on a meal allowance fills the employee, travel begin, travel
  end and customer from the trip if they are still empty. Values that were
  entered before the trip was selected are kept, and later changes of the trip
  dates do not change the dates of the meal allowance.
- Creating a new trip from the trip field of a meal allowance pre-fills the trip
  with the employee, description, customer and travel dates of the expense.
- Creating a trip from selected expenses (*Create Trip* action) extends the
  trip's date range with the travel dates of the selected meal allowances and
  uses their customer as the trip's customer.

The module is marked as `auto_install`, so it is installed automatically as soon
as both `hr_expense_meal_allowance` and `hr_expense_trip` are installed.
