import requests
import json
import os
import urllib
from hydroshare_his import settings
from lxml import etree


def get_layer_style(max_value, min_value, ndv_value, layer_id):
    """
    Sets default style for raster layers.
    """
    if ndv_value < min_value:
        low_ndv = f'<ColorMapEntry color="#000000" quantity="{ndv_value}" label="nodata" opacity="0.0" />'
        high_ndv = ""
    elif ndv_value > max_value:
        low_ndv = ""
        high_ndv = f'<ColorMapEntry color="#000000" quantity="{ndv_value}" label="nodata" opacity="0.0" />'
    else:
        low_ndv = ""
        high_ndv = ""
    layer_style = f"""<?xml version="1.0" encoding="ISO-8859-1"?>
    <StyledLayerDescriptor version="1.0.0" xmlns="http://www.opengis.net/sld" xmlns:ogc="http://www.opengis.net/ogc"
      xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
      xsi:schemaLocation="http://www.opengis.net/sld http://schemas.opengis.net/sld/1.0.0/StyledLayerDescriptor.xsd">
      <NamedLayer>
        <Name>simpleraster</Name>
        <UserStyle>
          <Name>{layer_id}</Name>
          <Title>Default raster style</Title>
          <Abstract>Default greyscale raster style</Abstract>
          <FeatureTypeStyle>
            <Rule>
              <RasterSymbolizer>
                <Opacity>1.0</Opacity>
                <ColorMap>
                  {low_ndv}
                  <ColorMapEntry color="#000000" quantity="{min_value}" label="values" />
                  <ColorMapEntry color="#FFFFFF" quantity="{max_value}" label="values" />
                  {high_ndv}
                </ColorMap>
              </RasterSymbolizer>
            </Rule>
          </FeatureTypeStyle>
        </UserStyle>
      </NamedLayer>
    </StyledLayerDescriptor>"""

    return layer_style


def get_geoserver_list(res_id):
    """
    Gets a list of data stores and coverages from a GeoServer workspace.
    """

    layer_list = []

    geoserver_namespace = settings.HIS.get("geoserver_ns")
    geoserver_url = settings.HIS.get("geoserver_url")
    geoserver_user = settings.HIS.get("geoserver_user")
    geoserver_pass = settings.HIS.get("geoserver_pass")
    geoserver_auth = requests.auth.HTTPBasicAuth(
        geoserver_user, 
        geoserver_pass
    )

    workspace_id = f"{geoserver_namespace}-{res_id}"

    headers = {
        "content-type": "application/json"
    }

    ds_rest_url = f"{geoserver_url}/workspaces/{workspace_id}/datastores.json"
    cv_rest_url = f"{geoserver_url}/workspaces/{workspace_id}/coverages.json"
    ds_response = requests.get(ds_rest_url, auth=geoserver_auth, headers=headers)
    cv_response = requests.get(cv_rest_url, auth=geoserver_auth, headers=headers)

    if ds_response.status_code == 200:
        ds_response_content = json.loads(ds_response.content)
        if ds_response_content.get("dataStores") and ds_response_content.get("dataStores") != "":
            for datastore in ds_response_content["dataStores"]["dataStore"]:
                layer_list.append((datastore["name"], "datastores"))

    if cv_response.status_code == 200:
        cv_response_content = json.loads(cv_response.content)
        if cv_response_content.get("coverages") and cv_response_content.get("coverages") != "":
            for coverage in cv_response_content["coverages"]["coverage"]:
                layer_list.append((coverage["name"], "coveragestores"))

    return layer_list


def get_hydroserver_list(res_id):
    """
    Gets a list of data stores and coverages from a GeoServer workspace.
    """

    database_list = []

    hydroserver_url = settings.HIS.get("hydroserver_url")

    if hydroserver_url is not None:
        rest_url = f"{hydroserver_url}/manage/network/{res_id}/databases/"
        response = requests.get(rest_url)

        if response.status_code == 200:
            response_content = json.loads(response.content)
            for database in response_content:
                database_list.append(database["database_id"])

    return database_list


def get_database_list(res_id):
    """
    Gets a list of HydroShare databases on which web services can be published.
    """

    db_list = {
        "access": None,
        "geoserver": {
            "create_workspace": True,
            "register": [],
            "unregister": []
        },
        "hydroserver": {
            "create_network": True,
            "register": [],
            "unregister": []
        }
    }

    hydroshare_url = settings.HIS.get("hydroshare_url")
    rest_url = f"{hydroshare_url}/resource/{res_id}/file_list/"
    response = requests.get(rest_url)

    if response.status_code != 200:
        db_list["access"] = "private"
        return db_list
    else:
        db_list["access"] = "public"

    file_list = json.loads(response.content.decode('utf-8'))["results"]

    geoserver_list = get_geoserver_list(res_id)
    if geoserver_list:
        db_list["geoserver"]["create_workspace"] = False

    hydroserver_list = get_hydroserver_list(res_id)
    if hydroserver_list:
        db_list["hydroserver"]["create_network"] = False

    registered_list = []

    for result in file_list:
        if (
                result["logical_file_type"] == "GeoRasterLogicalFile" and 
                result["content_type"] == "image/tiff" and 
                settings.HIS.get("geoserver_url") is not None
            ) or (
                result["logical_file_type"] == "GeoFeatureLogicalFile" and 
                result["content_type"] == "application/x-qgis" and
                settings.HIS.get("geoserver_url") is not None
            ):

            layer_name = "/".join(result["url"].split("/")[7:-1])
            layer_path = "/".join(result["url"].split("/")[4:])
            file_name = ".".join(result["url"].split("/")[-1].split(".")[:-1])
            layer_ext = result["url"].split("/")[-1].split(".")[-1]
            layer_type = result["content_type"]
            if result["content_type"] == "image/tiff" and layer_ext == "tif":
                registered_list.append(layer_name.replace("/", " "))
                if layer_name.replace("/", " ") not in [i[0] for i in geoserver_list]:
                    db_list["geoserver"]["register"].append(
                        {
                            "layer_name": layer_name,
                            "layer_type": "GeographicRaster",
                            "file_name": file_name,
                            "file_type": "geotiff",
                            "hs_path": layer_path,
                            "store_type": "coveragestores",
                            "layer_group": "coverages",
                            "verification": "coverage"
                        }
                    )
            if result["content_type"] == "application/x-qgis" and layer_ext == "shp":
                registered_list.append(layer_name.replace("/", " "))
                if layer_name.replace("/", " ") not in [i[0] for i in geoserver_list]:
                    db_list["geoserver"]["register"].append(
                        {
                            "layer_name": layer_name,
                            "layer_type": "GeographicFeature",
                            "file_name": file_name,
                            "file_type": "shp",
                            "hs_path": layer_path,
                            "store_type": "datastores",
                            "layer_group": "featuretypes",
                            "verification": "featureType"
                        }
                    )

        elif (
                result["logical_file_type"] == "TimeSeriesLogicalFile" and 
                result["url"].split("/")[-1].split(".")[-1] in ("sqlite", "db") and
                settings.HIS.get("hydroserver_url") is not None
            ):

            layer_name = "/".join(result["url"].split("/")[7:-1])
            registered_list.append(layer_name)

            if layer_name not in hydroserver_list:
                db_list["hydroserver"]["register"].append(
                    {
                        "database_name": layer_name,
                        "hs_path": "/".join(result["url"].split("/")[4:]),
                        "layer_title": ".".join(result["url"].split("/")[-1].split(".")[:-1])
                    }
                )

    for layer in geoserver_list:
        if layer[0] not in registered_list:
            db_list["geoserver"]["unregister"].append(
                {
                    "layer_name": layer[0],
                    "store_type": layer[1]
                }
            )

    for database in hydroserver_list:
        if database not in registered_list:
            db_list["hydroserver"]["unregister"].append(
                {
                    "database_name": database
                }
            )

    if not db_list["geoserver"]["register"]:
        db_list["geoserver"]["create_workspace"] = False

    if not db_list["hydroserver"]["register"]:
        db_list["hydroserver"]["create_network"] = False

    return db_list


def register_geoserver_workspace(res_id):
    """
    Add GeoServer workspace.
    """

    geoserver_namespace = settings.HIS.get("geoserver_ns")
    geoserver_url = settings.HIS.get("geoserver_url")
    geoserver_user = settings.HIS.get("geoserver_user")
    geoserver_pass = settings.HIS.get("geoserver_pass")
    geoserver_auth = requests.auth.HTTPBasicAuth(
        geoserver_user, 
        geoserver_pass
    )

    workspace_id = f"{geoserver_namespace}-{res_id}"

    unregister_geoserver_databases(res_id)

    headers = {
        "content-type": "application/json"
    }

    data = json.dumps({"workspace": {"name": workspace_id}})
    rest_url = f"{geoserver_url}/workspaces"
    response = requests.post(rest_url, headers=headers, data=data, auth=geoserver_auth)

    return workspace_id


def register_hydroserver_network(res_id):
    
    hydroserver_url = settings.HIS.get("hydroserver_url")
    hydroserver_user = settings.HIS.get("hydroserver_user")
    hydroserver_pass = settings.HIS.get("hydroserver_pass")
    hydroserver_auth = requests.auth.HTTPBasicAuth(
        hydroserver_user, 
        hydroserver_pass
    )

    unregister_hydroserver_databases(res_id)

    rest_url = f"{hydroserver_url}/manage/networks/"

    data = {
        "network_id": res_id
    }

    response = requests.post(rest_url, data=data, auth=hydroserver_auth)

    return response


def unregister_geoserver_databases(res_id):
    """
    Removes a GeoServer network and associated databases.
    """

    geoserver_namespace = settings.HIS.get("geoserver_ns")
    geoserver_url = settings.HIS.get("geoserver_url")
    geoserver_user = settings.HIS.get("geoserver_user")
    geoserver_pass = settings.HIS.get("geoserver_pass")
    geoserver_auth = requests.auth.HTTPBasicAuth(
        geoserver_user, 
        geoserver_pass
    )

    workspace_id = f"{geoserver_namespace}-{res_id}"

    headers = {
        "content-type": "application/json"
    }

    params = {
        "update": "overwrite", "recurse": True
    }

    rest_url = f"{geoserver_url}/workspaces/{workspace_id}"

    if geoserver_url is not None:
        response = requests.delete(rest_url, params=params, auth=geoserver_auth, headers=headers)
    else:
        response = None

    return response


def unregister_hydroserver_databases(res_id):
    """
    Removes a HydroServer network and associated databases.
    """

    hydroserver_url = settings.HIS.get("hydroserver_url")
    hydroserver_user = settings.HIS.get("hydroserver_user")
    hydroserver_pass = settings.HIS.get("hydroserver_pass")
    hydroserver_auth = requests.auth.HTTPBasicAuth(
        hydroserver_user,
        hydroserver_pass
    )

    rest_url = f"{hydroserver_url}/manage/network/{res_id}/"

    if hydroserver_url is not None:
        response = requests.delete(rest_url, auth=hydroserver_auth)
    else:
        response = None

    return response


def register_geoserver_db(res_id, db):
    """
    Attempts to register a GeoServer layer
    """

    geoserver_namespace = settings.HIS.get("geoserver_ns")
    geoserver_url = settings.HIS.get("geoserver_url")
    geoserver_user = settings.HIS.get("geoserver_user")
    geoserver_directory = settings.HIS.get("geoserver_data_dir")
    geoserver_pass = settings.HIS.get("geoserver_pass")
    geoserver_auth = requests.auth.HTTPBasicAuth(
        geoserver_user, 
        geoserver_pass
    )

    workspace_id = f"{geoserver_namespace}-{res_id}"

    headers = {
        "content-type": "application/json"
    }

    if any(i in db['layer_name'] for i in [".", ","]):
        return {"success": False, "type": db["layer_type"], "layer_name": db["layer_name"], "message": "Error: Unable to register GeoServer layer."}

    rest_url = f"{geoserver_url}/workspaces/{workspace_id}/{db['store_type']}/{db['layer_name'].replace('/', ' ')}/external.{db['file_type']}"
    data = f"file://{geoserver_directory}/{db['hs_path']}"
    response = requests.put(rest_url, data=data, headers=headers, auth=geoserver_auth)

    if response.status_code != 201:
        return {"success": False, "type": db["layer_type"], "layer_name": db["layer_name"], "message": "Error: Unable to register GeoServer layer."}

    rest_url = f"{geoserver_url}/workspaces/{workspace_id}/{db['store_type']}/{db['layer_name'].replace('/', ' ')}/{db['layer_group']}/{db['file_name']}.json"
    response = requests.get(rest_url, headers=headers, auth=geoserver_auth)

    try:
        if json.loads(response.content.decode('utf-8'))[db["verification"]]["enabled"] is False:
            return {"success": False, "type": db["layer_type"], "layer_name": db["layer_name"], "message": "Error: Unable to register GeoServer layer."}
    except:
        return {"success": False, "type": db["layer_type"], "layer_name": db["layer_name"], "message": "Error: Unable to register GeoServer layer."}

    bbox = json.loads(response.content)[db["verification"]]["nativeBoundingBox"]

    data = response.content.decode('utf-8').replace('"name":"' + db["file_name"] + '"', '"name":"' + db["layer_name"].replace("/", " ") + '"')
    response = requests.put(rest_url, headers=headers, auth=geoserver_auth, data=data)

    if response.status_code != 200:
        return {"success": False, "type": db["layer_type"], "layer_name": db["layer_name"], "message": "Error: Unable to register GeoServer layer."}

    if db["layer_type"] == "GeographicRaster":
        try:
            hydroshare_url = "/".join(settings.HIS.get("hydroshare_url").split("/")[:-1])
            layer_vrt_url = f"{hydroshare_url}/resource/{'.'.join(db['hs_path'].split('.')[:-1])}.vrt"
            response = requests.get(layer_vrt_url)
            vrt = etree.fromstring(response.content.decode('utf-8'))
            layer_max = None
            layer_min = None
            layer_ndv = None
            for element in vrt.iterfind(".//MDI"):
                if element.get("key") == "STATISTICS_MAXIMUM":
                    layer_max = element.text
                if element.get("key") == "STATISTICS_MINIMUM":
                    layer_min = element.text

            if layer_max == None or layer_min == None or layer_min >= layer_max:
                return {"success": False, "type": db["layer_type"], "layer_name": db["layer_name"], "message": "Error: Unable to parse VRT file."}

            try:
                layer_ndv = vrt.find(".//NoDataValue").text
            except:
                return {"success": False, "type": db["layer_type"], "layer_name": db["layer_name"], "message": "Error: Unable to parse VRT file."}

            if layer_ndv == None:
                return {"success": False, "type": db["layer_type"], "layer_name": db["layer_name"], "message": "Error: Unable to parse VRT file."}

            layer_style = get_layer_style(layer_max, layer_min, layer_ndv, db["layer_name"].replace("/", " "))

            rest_url = f"{geoserver_url}/workspaces/{workspace_id}/styles"
            headers = {"content-type": "application/vnd.ogc.sld+xml"}
            response = requests.post(rest_url, data=layer_style, auth=geoserver_auth, headers=headers)

            if response.status_code != 201:
                return {"success": False, "type": db["layer_type"], "layer_name": db["layer_name"], "message": "Error: Unable to parse VRT file."}

            rest_url = f"{geoserver_url}/layers/{workspace_id}:{db['layer_name'].replace('/', ' ')}"
            headers = {"content-type": "application/json"}
            body = '{"layer": {"defaultStyle": {"name": "' + db["layer_name"].replace("/", " ") + '", "href":"https:\/\/geoserver.hydroshare.org\/geoserver\/rest\/styles\/' + db["layer_name"].replace("/", " ") + '.json"}}}'
            response = requests.put(rest_url, data=body, auth=geoserver_auth, headers=headers)

            if response.status_code != 200:
                return {"success": False, "type": db["layer_type"], "layer_name": db["layer_name"], "message": "Error: Unable to parse VRT file."}
        except:
            return {"success": False, "type": db["layer_type"], "layer_name": db["layer_name"], "message": "Error: Unable to parse VRT file."}

    return {"success": True, "type": db["layer_type"], "layer_name": db["layer_name"], "message": f"{'/'.join((geoserver_url.split('/')[:-1]))}/{workspace_id}/wms?service=WMS&version=1.1.0&request=GetMap&layers={workspace_id}:{urllib.parse.quote(db['layer_name'].replace('/', ' '))}&bbox={bbox['minx']}%2C{bbox['miny']}%2C{bbox['maxx']}%2C{bbox['maxy']}&width=612&height=768&srs={bbox['crs']}&format=application/openlayers"}


def unregister_geoserver_db(res_id, db):
    """
    Removes a GeoServer layer
    """

    geoserver_namespace = settings.HIS.get("geoserver_ns")
    geoserver_url = settings.HIS.get("geoserver_url")
    geoserver_user = settings.HIS.get("geoserver_user")
    geoserver_pass = settings.HIS.get("geoserver_pass")
    geoserver_auth = requests.auth.HTTPBasicAuth(
        geoserver_user, 
        geoserver_pass
    )

    workspace_id = f"{geoserver_namespace}-{res_id}"

    headers = {
        "content-type": "application/json"
    }

    params = {
        "update": "overwrite", "recurse": True
    }

    if geoserver_url is not None:
        rest_url = f"{geoserver_url}/workspaces/{workspace_id}/{db['store_type']}/{db['layer_name'].replace('/', ' ')}"
        response = requests.delete(rest_url, params=params, headers=headers, auth=geoserver_auth)
    else:
        response = None

    return response


def register_hydroserver_db(res_id, db):

    hydroserver_url = settings.HIS.get("hydroserver_url")
    hydroserver_user = settings.HIS.get("hydroserver_user")
    hydroserver_pass = settings.HIS.get("hydroserver_pass")
    hydroserver_data_dir = settings.HIS.get("hydroserver_data_dir")
    hydroserver_auth = requests.auth.HTTPBasicAuth(
        hydroserver_user, 
        hydroserver_pass
    )

    rest_url = f"{hydroserver_url}/manage/network/{res_id}/databases/"

    db_path = f"{hydroserver_data_dir}/{db['hs_path']}"
    data = {
        "network_id": str(res_id),
        "database_id": str(db["database_name"]),
        "database_name": str(db["layer_title"]),
        "database_path": str(db_path),
        "database_type": "odm2_sqlite"
    }

    response = requests.post(rest_url, data=data, auth=hydroserver_auth)

    if response.status_code != 201:
        return {"success": False, "type": "Timeseries", "message": "Error: Unable to register Water Data Server database."}

    return {"success": True, "type": "Timeseries", "message": f"{hydroserver_url}/refts/catalog/?network_id={res_id}&database_id={db['database_name']}"}


def unregister_hydroserver_db(res_id, db):
    """
    Removes a HydroServer database.
    """

    hydroserver_url = settings.HIS.get("hydroserver_url")
    hydroserver_user = settings.HIS.get("hydroserver_user")
    hydroserver_pass = settings.HIS.get("hydroserver_pass")
    hydroserver_auth = requests.auth.HTTPBasicAuth(
        hydroserver_user,
        hydroserver_pass
    )

    rest_url = f"{hydroserver_url}/manage/network/{res_id}/database/{db['database_name']}/"

    if hydroserver_url is not None:
        response = requests.delete(rest_url, auth=hydroserver_auth)
    else:
        response = None

    return(response)


def build_hydroshare_response(res_id, registered_services, geoserver_list, hydroserver_list):

    response = {
        "resource": {},
        "content": []
    }

    geoserver_namespace = settings.HIS.get("geoserver_ns")
    geoserver_url = settings.HIS.get("geoserver_url")
    workspace_id = f"{geoserver_namespace}-{res_id}"
    hydroserver_url = settings.HIS.get("hydroserver_url")


    if geoserver_list:
        response["resource"]["WMS Endpoint"] = f"{'/'.join((geoserver_url.split('/')[:-1]))}/wms?service=WMS&version=1.3.0&request=GetCapabilities&namespace={workspace_id}"

    if "datastores" in [i[1] for i in geoserver_list]:
        response["resource"]["WFS Endpoint"] = f"{'/'.join((geoserver_url.split('/')[:-1]))}/wfs?service=WFS&version=1.1.0&request=GetCapabilities&namespace={workspace_id}"

    if "coveragestores" in [i[1] for i in geoserver_list]:
        response["resource"]["WCS Endpoint"] = f"{'/'.join((geoserver_url.split('/')[:-1]))}/wcs?service=WCS&version=1.1.0&request=GetCapabilities&namespace={workspace_id}"

    if hydroserver_list:
        response["resource"]["WOF Endpoint"] = f"{hydroserver_url}/refts/catalog/?network_id={res_id}"

    for i in registered_services["geoserver"]:
        response["content"].append(i)

    for i in registered_services["hydroserver"]:
        response["content"].append(i)

    return response
