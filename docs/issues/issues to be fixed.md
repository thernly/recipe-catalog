# Recipe Catalog - Issues to be fixed

## UI/UX

### Inconsistencies

- The navigation bar appears twice on `Export` page.
- On the `Settings` page under `Danger Zone` there is a label `Delete Account`, but no action can be taken.  If this has been implemented, then a button needs to be added to allow the user to take action.
- On the recipe pages, the contrast of the butttons (Edit, Duplicate, Export, and Print) is low against the background, making them hard to see.
- On the settings page, on statistics, imported, manual entry, and "this month" all have undefined values.  These should never be undefined.  They should be zero if there is no data.  There is also a box with a person icon that has the value "null" displayed.  If this is supposed to be a name, then if no name is provided it should just display blank.
