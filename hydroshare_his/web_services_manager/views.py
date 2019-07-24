from rest_framework.response import Response
from rest_framework import viewsets, status
from rest_framework.permissions import BasePermission, IsAuthenticated, SAFE_METHODS
from web_services_manager import utilities
import json


class ReadOnly(BasePermission):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS


class Services(viewsets.ViewSet):
    """
    Services

    Test
    """

    permission_classes = (IsAuthenticated|ReadOnly,)

    def post_update_services(self, request, resource_id, *args, **kwargs):
        """
        Checks HydroShare resource for data that can be exposed via WMS, WFS, WCS, or WOF web services,
        publishes those services, then returns access URLs to HydroShare.
        """

        db_list_response = utilities.get_database_list(resource_id)

        registered_services = {
            "geoserver": [],
            "hydroserver": []
        }

        if db_list_response["access"] == ("private" or "not_found"):

            utilities.unregister_geoserver_databases(resource_id)
            utilities.unregister_hydroserver_databases(resource_id)

            return Response(None, status=status.HTTP_201_CREATED)

        elif db_list_response["access"] == "public":

            if db_list_response["geoserver"]["create_workspace"]:
                utilities.register_geoserver_workspace(resource_id)

            if db_list_response["hydroserver"]["create_network"]:
                utilities.register_hydroserver_network(resource_id)

            for db in db_list_response["geoserver"]["unregister"]:
                utilities.unregister_geoserver_db(resource_id, db)

            for db in db_list_response["geoserver"]["register"]:
                db_info = utilities.register_geoserver_db(resource_id, db)
                if db_info["success"] is False:
                    utilities.unregister_geoserver_db(resource_id, db)
                else:
                    registered_services["geoserver"].append(db_info)

            for db in db_list_response["hydroserver"]["unregister"]:
                utilities.unregister_hydroserver_db(resource_id, db)

            for db in db_list_response["hydroserver"]["register"]:
                db_info = utilities.register_hydroserver_db(resource_id, db)
                if db_info["success"] is False:
                    utilities.unregister_geoserver_db(resource_id, db)
                else:
                    registered_services["hydroserver"].append(db_info)

            geoserver_list = utilities.get_geoserver_list(resource_id)

            if not geoserver_list:
                utilities.unregister_geoserver_databases(resource_id)

            hydroserver_list = utilities.get_hydroserver_list(resource_id)

            if not hydroserver_list:
                utilities.unregister_hydroserver_databases(resource_id)

            response = utilities.build_hydroshare_response(resource_id, registered_services, geoserver_list, hydroserver_list)

            return Response(response, status=status.HTTP_201_CREATED)
