Test Automation
===============

Rest API Smoke Test
-------------------

Smoke test script **rest_api_smoke_test.py** performs the following action over Rest API:
- Admin (webadmin) creates Tenant with name = smoke_tenant
- Admin creates User with name = smoke_user
- The created user (smoke_user) makes the following actions via POST/PUT/DELETE Sessions; 
 - Login
 - Set State to 'Available'/'Unavailable'
 - Logout
- Admin delete both User and Tenant

###How to run the script:

1. Create the Development Environment, build and start Apollo:
```
    $> cd <apollo-project-root>
    $> vagrant ssh
```
```
    host-vm $> make release
    host-vm $> make run
```
The script uses python external module: requests.
Update vagrant provision or just invoke "sudo yum install python-requests" on the virual host.

2. Add admin user to be used in the test for tenant and user creation:
```
    elnang$> wcs_utils:debug_create_admin().
```

3. Start the test:
```
     host-vm $> make smoke-test
```
or manually:
```
     host-vm $> python /apollo/automation/rest_api_smoke_test.py -s <core_server>:<web_port>
```

###Result:

The script returns __TEST PASSED__ with exit code “0” on success; or __TEST FAILED__  with exit code “1” if something wrong has happened.

The script run leaves the log file in folder /apollo/automation/log.

