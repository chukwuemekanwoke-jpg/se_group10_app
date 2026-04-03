## Development Workflow
## Branch note
This deploy branch is based on `feature-route-refresh` and includes the login page work for integration with the current app structure.

This branch adds the first working version of the login and registration feature.

Included work:
- Added `login.html` and `register.html`
- Added related CSS and JS files
- Added `/login` and `/register` routes in Flask
- Added backend registration and login handling
- Added password hashing for secure storage
- Added a `users` table to the database schema in `sql/init.sql`
- Connected successful login to the existing map page

The registration flow has been tested successfully with data stored in the database.
