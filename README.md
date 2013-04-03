Test Automation
===============

Rest API Smoke Test
-------------------

Smoke test script **rest_api_smoke_test.py** performs the following action over Rest API:
- Admin (webadmin) creates Tenant with name = smoke_tenant
- Admin creates User with name = smoke_user
- The created user (smoke_user) makes Login and Logout via POST/PUT/DELETE Sessions; 
 - Login
 - Set State to 'Available'/'Unavailable'
 - Logout
- Admin delete both User and Tenant

###How to run the script:
1.
Create your Development Environment, build and start Apollo as described in [devev bootstrap](https://github.com/Five9/devenv-bootstrap)
 
    $> cd <apollo-project-root>
    $> vagrant ssh

    host-vm $> make release
    host-vm $> make run

2.
Add admin user to be used in the test for tenant and user creation:

    elnang$> wcs_utils:debug_create_admin().

3.
Start the test:

     host-vm $> make smoke-test

To get terminal access on the running Apollo vm, run the command
`vagrant ssh` in the apollo directory.

    $> cd <apollo-project-root>
    $> vagrant ssh

 This will ssh into the apollo host as the `vagrant` user. This user
has full sudo authority.
