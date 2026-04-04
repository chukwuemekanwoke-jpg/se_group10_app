## Branch Update

This branch adds the initial working authentication flow to the current app structure.

Changes made in this branch include:

- Added a login page (`login.html`) and a register page (`register.html`)
- Added matching frontend styling files for both pages (`login.css`, `register.css`)
- Added Flask routes for:
  - `/`
  - `/login`
  - `/register`
  - `/index`
  - `/map`
- Updated the page flow so that:
  - the default entry point `/` redirects to the login page
  - successful login redirects the user to the main page (`index.html`)
  - if a user does not exist, they are guided to register first
- Copied the main map interface structure into `index.html`, which is now used as the main front-end page
- Implemented backend registration logic:
  - validates required fields
  - checks for duplicate email addresses
  - hashes the password before storing it
  - inserts the new user into the database
- Implemented backend login logic:
  - checks whether the user exists
  - verifies the hashed password
  - only allows valid login to proceed to the main page
- Added flash message support for login/register feedback
- Added a `users` table to the database schema in `sql/init.sql`

### Users table fields
- `id`
- `first_name`
- `last_name`
- `email`
- `phone_number`
- `password_hash`
- `created_at`

### Current status
- Registration has been tested successfully with data stored in the database
- Login now correctly validates credentials before redirecting
- The app now follows the intended page flow: Login → Register (if needed) → Index