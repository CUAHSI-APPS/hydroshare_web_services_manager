# HydroShare Web Services Manager

This application managers HydroShare web data services by registering resource content on systems like GeoServer and HydroServer. It has been designed to support HydroShare data service capabilities by linking HydroShare data to data servers in real time. A prebuilt docker image is available on Docker Hub at https://cloud.docker.com/repository/docker/kjlippold/hydroshare_web_services_manager.

## Getting Started

These instructions will help you install and run this application in a production environment.

### Prerequisites

##### Docker:
* [Install Docker Engine](https://docs.docker.com/install/)

##### GeoServer:
* [Install GeoServer](https://github.com/kjlippold/his_geoserver#his-geoserver)

##### HydroServer:
* [Install HydroServer](https://github.com/kjlippold/his_hydroserver#his-hydroserver)

### Installing
Run Web Services Manager Docker instance:
```
$ sudo docker run -d -p {host_port}:8060 -v /static/his/:/static/his/ --name hydroshare_web_services_manager 
```

Enter the Web Services Manager container:
```
$ sudo docker exec -it hydroshare_web_services_manager /bin/bash
```

Edit Web Services Manager settings:
```
$ sudo vi /home/hisapp/hydroshare_his/hydroshare_his/settings.py
```

Add your host URL to CSRF_TRUSTED_ORIGINS, CSRF_COOKIE_DOMAIN, and ALLOWED_HOSTS. Set DEBUG to False for production environments. Edit the STATIC_URL and STATIC_ROOT to point to your static files on the container and on the host. Change the PROXY_BASE_URL to {host_url}/wds.

The HIS setting should include connection information to GeoServer, HydroServer, and HydroShare REST APIs (e.g. "https://beta.hydroshare.org/hsapi" for hydroshare_url, "https://geoserver-beta.hydroshare.org/geoserver/rest" for geoserver_url, and "https://geoserver-beta.hydroshare.org/wds" for hydroserver_url). The GeoServer namespace setting is used to preceed GeoServer workspace names, and must start with a letter (e.g. "HS-"). The data directory settings for both GeoServer and HydroServer should match the path inside each of those containers to the mounted HydroShare resource directory. Finally, usernames and passwords for GeoServer and HydroServer should be provided to give the web services manager POST and DELETE permissions for those servers. 

Save and close the file:
```
:wq
```

Exit the container:
```
$ exit
```

Restart the Web Services Manager:
```
$ sudo docker restart hydroshare_web_services_manager
```

The default username and password are admin, hydroshare. From the admin page of the Web Services Manager ({hostname}/his/), change the admin password. Create a new admin token to be given to HydroShare.

To connect this service to HydroShare, some settings must be edited in HydroShare's local_settings.py file. HSWS_URL should point to the Web Service Manager update endpoint (e.g. "https://geoserver.hydroshare.org/his/services/update"). HSWS_API_TOKEN should be set to the token value created in the previous step. HSWS_TIMEOUT should be set to tell HydroShare how long to wait for a response from the Web Services Manager. HSWS_PUBLISH_URLS should be set to True if you wish to publish data service connection URLs on HydroShare's resource landing page as extra metadata. HSWS_ACTIVATED should be set to True to tell HydroShare to send signals to the Web Services Manager.

## Built With

* [Docker](https://docs.docker.com) - Docker Engine
* [Django](https://www.djangoproject.com) - Python Web Framework
* [Gunicorn](https://gunicorn.org) - WSGI HTTP Server

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details