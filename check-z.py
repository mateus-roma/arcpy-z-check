# ##########################################################################################
#
# -- Desenvolvido por MATEUS ROMANHOLI (2015)
#
# ##########################################################################################

import arcpy
import pythonaddins

class cbLinhas(object):
    def __init__(self):
        self.editable = True
        self.enabled = True
        self.dropdownWidth = 'WWWWWWWWWWWWWW'
        self.width = 'WWWWWWWWWWWWWW'
    def onSelChange(self, selection):
        global inLineFClass
        inLineFClass = selection
    def onEditChange(self, text):
        global inLineFClass
        inLineFClass = text
    def onFocus(self, focused):
         # When the combo box has focus, update the combo box with the list of layer names.
    	if focused:
    		self.mxd = arcpy.mapping.MapDocument('current')
    		layers = arcpy.mapping.ListLayers(self.mxd)
    		self.items = []
    		for layer in layers:
                    if arcpy.Describe(layer).featureClass.shapeType == "Polyline":
                        self.items.append(layer.name)
    def onEnter(self):
        pass
    def refresh(self):
        pass

class cbAreas(object):
    def __init__(self):
        self.editable = True
        self.enabled = True
        self.dropdownWidth = 'WWWWWWWWWWWWWW'
        self.width = 'WWWWWWWWWWWWWW'
    def onSelChange(self, selection):
        global inAreaFClass
        inAreaFClass = selection
    def onEditChange(self, text):
        global inAreaFClass
        inAreaFClass = text
    def onFocus(self, focused):
         # When the combo box has focus, update the combo box with the list of layer names.
    	if focused:
    		self.mxd = arcpy.mapping.MapDocument('current')
    		layers = arcpy.mapping.ListLayers(self.mxd)
    		self.items = []
    		for layer in layers:
                    if arcpy.Describe(layer).featureClass.shapeType == "Polygon":
                        self.items.append(layer.name)
    def onEnter(self):
        pass
    def refresh(self):
        pass

class cbPastaSaida(object):
    def __init__(self):
        self.editable = True
        self.enabled = True
        self.dropdownWidth = 'WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW'
        self.width = 'WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW'
    def onSelChange(self, selection):
        pass
    def onEditChange(self, text):
        global outFolder
        outFolder = text
        self.onEnter()
        self.refresh()
    def onFocus(self, focused):
        pass
    def onEnter(self):
        pass
    def refresh(self):
        pass

class btExecuta(object):
    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):
        # _____ DEFINE FUNCTIONS _____ #

        # Function to check if vertex Z values are descending from source to mouth for draiange stretchs
        # The inputs are a list of vertices for each feature, a list to hold point geometries for errors,
            # a spatial reference system and a Z tolerance value
        def LineAscendingZCheck(vertexlist, pointgeometrylist, sr, ztolerance):
            vertexCount = 0

            # Iterates through the list of vertices for each feature, until the second to last. Each vertex holds 3 coordinates.
            while vertexCount < len(vertexlist) - 1:

                currVertex = vertexlist[vertexCount]
                nextVertex = vertexlist[vertexCount + 1]

                for i, coord in enumerate(currVertex):

                    # Compare the Z coordinate of the current vertex to the Z coordinate of the next vertex
                    if i == 2:
                        if (round((round(coord, 3) - round(nextVertex[2], 3)),3)) <= (ztolerance * (-1)):

                            # Creates a point object if the Z coord of the current vertex is lower than the next's
                            point = arcpy.Point(currVertex[0], currVertex[1], currVertex[2])

                            # Creates a point geometry object for each error found and appends it to the list that holds all the error points coords
                            pointGeometry = arcpy.PointGeometry(point, sr)
                            pointgeometrylist.append(pointGeometry)

                        else:
                            pass
                    else:
                        pass
                vertexCount += 1

        # Function to check if vertex Z values are constant for water masses
        # The inputs are a list of vertices for each feature, a list to hold point geometries for errors,
            # a spatial reference system and a Z tolerance value
        def AreaConstantZCheck(vertexlist, pointgeometrylist, sr, ztolerance):

            # Imports module to calculate most commom value for Z coordinates
            from collections import Counter

            vertexCount = 0

            # Creates list to hold all Z coordinates from the polygon
            zCoordList = []

            # Appends all all Z coordinates from the polygon to the list
            for vertex in vertexlist:
                zCoordList.append(vertex[2])

            # If all Z coordinates are equal, do nothing
            if all(zCoord == zCoordList[0] for zCoord in zCoordList):
                pass

            # Else, calculates most commom value for Z coordinates
            else:
                coordCounter = Counter(zCoordList)
                coordMode = ((coordCounter.most_common(1))[0])[0]

                # For each vertex in the list...
                while vertexCount < len(vertexlist):

                    # ...sets it as the current vertex
                    currVertex = vertexlist[vertexCount]

                    # Iterates through the vertex's coordinates
                    for i, coord in enumerate(currVertex):

                        # Compare the Z coordinate of the current vertex to the most commom Z coordinate value
                        if i == 2:

                            # Checks to see if the difference between the current vertex's Z coord and the most commom Z coord value
                                # is higher than the user specified tolerance
                            if abs(round((coord - coordMode),3)) >= ztolerance:

                                # Creates a point object if the previous check results true
                                point = arcpy.Point(currVertex[0], currVertex[1], currVertex[2])

                                # Creates a point geometry object for each error found and appends it to the list
                                    # that holds all the error points coords
                                pointGeometry = arcpy.PointGeometry(point, sr)
                                pointgeometrylist.append(pointGeometry)

                            else:
                                pass
                        else:
                            pass

                    vertexCount += 1


        # _____ MAIN CODE BODY _____ #

        import os
        import locale

        locale.setlocale(locale.LC_ALL, "portuguese_Brazil")

        zTolerance = 0.001

        arcpy.env.overwriteOutput = True

        # Creates an empty list to hold the coordinates of the error points
        pointGeometryList = []

        try:
            # Checks to see if there is a line feature class input
            if hasattr(arcpy.Describe(inLineFClass), "name"):

                    # Gets the spatial reference from the line feature class
                    spatialRef = arcpy.Describe(inLineFClass).SpatialReference

                    # Opens a search cursor on the input line feature class
                    for row in arcpy.da.SearchCursor(inLineFClass, ["OID@", "SHAPE@"]):

                        # Gets feature geometry
                        feat = row[1]

                        # Tests to see if the geometry in not null (thus invalid)
                        if feat is not None:

                            # If the feature is not null (has geometry), creates an empty list to hold its vertices
                            for part in feat:
                                vertexList = []

                                # Iterates through the feature's vertices and appends their coordinates to the vertex list
                                for pnt in part:
                                    vertexList.append([pnt.X, pnt.Y, pnt.Z])

                                # Feeds the vertex list, the empty error point geometry list and the spatial reference system to the function
                                LineAscendingZCheck(vertexList, pointGeometryList, spatialRef, zTolerance)

                        # If the feature's geometry is null, adds message to the window telling its OID
                        else:
                            arcpy.AddMessage("AVISO: Linha de ID {0} nao tem geometria".format(row[0]))

            # If there is no input line feature class, go on through the code
            else:
                pass

        except:
            pass

        try:
            # Checks to see if there is an area feature class input
            if hasattr(arcpy.Describe(inAreaFClass), "name"):

                    # Gets the spatial reference from the area feature class
                    spatialRef = arcpy.Describe(inAreaFClass).SpatialReference

                    # Opens a search cursor on the input area feature class
                    for row in arcpy.da.SearchCursor(inAreaFClass, ["OID@", "SHAPE@"]):

                        # Gets feature geometry
                        feat = row[1]

                        # Tests to see if the geometry in not null (thus invalid)
                        if feat is not None:

                            # If the feature is not null (has geometry), creates an empty list to hold its vertices
                            vertexList = []

                            # Iterates through each part in the feature
                            for part in feat:

                                # Iterates through the feature's vertices
                                for pnt in part:

                                    # Appends the feature's coordinates to the vertex list
                                    if pnt:
                                        vertexList.append([pnt.X, pnt.Y, pnt.Z])

                                    # If there's no vertex (start of an interior ring), pass on
                                    else:
                                        pass

                            # Feeds the vertex list, the empty error point geometry list, the spatial reference system and the Z tolerance to the function
                            AreaConstantZCheck(vertexList, pointGeometryList, spatialRef, zTolerance)

                        # If the feature's geometry is null, adds message to the window telling its OID
                        else:
                            pythonaddins.MessageBox("Poligono de ID {0} nao tem geometria".format(row[0]), "AVISO")

            # If there is no input area feature class, go on through the code
            else:
                pass

        except:
            pass

        # If the error points list returned by the function is not empty, creates a feature class with the error points to be opened in ArcMap
        if len(pointGeometryList) > 0:
            outFC = os.path.join(outFolder, "ERRO_EM_Z.shp")
            arcpy.CopyFeatures_management(pointGeometryList, outFC)

            arcpy.SetParameterAsText(0, outFC)
        else:
            pythonaddins.MessageBox("Nao foram encontrados erros!", "AVISO")