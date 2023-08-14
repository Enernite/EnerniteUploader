""" 

Author: Marius Hofgaard 
Copyright Enernite 2023

Layer preparation for Enernite Uploader for QGIS


"""


import os
from qgis.core import QgsSymbol, QgsVectorFileWriter, QgsRasterFileWriter, QgsVectorLayer, QgsRasterLayer,QgsMapLayer,QgsMapLayerStyleManager, QgsCoordinateTransform, QgsCoordinateReferenceSystem, QgsWkbTypes
from PyQt5.QtCore import QObject
import tempfile
from qgis.PyQt.QtCore import (
    QVariant,
    QObject
)

import random 

from .exceptions import LayerPackagingException


class LayerExporter(QObject):
    def __init__(self, transform_context):
        super().__init__()
        self.transform_context = transform_context
        self.temp_dir =  tempfile.mkdtemp() 
        

    @staticmethod
    def can_export_layer(layer: QgsMapLayer) -> bool:
        # Check if the layer is exportable (vector or raster)
        # and meets specific criteria
        """
        Returns True if a layer can be exported
        """
        if isinstance(layer, QgsVectorLayer):
            return True 

        if isinstance(layer, QgsRasterLayer):
            # We cannot handle rasters at the current point.
            return False

        return False


    @staticmethod
    def representative_layer_style(layer):
        # Determine representative style for a vector layer
        # Extract styling information from renderer and symbol

        # We want to get the fill color and the stroke color.

        # Get the layer by name from the project

        # This is a simplified method, and only works for simple fill colors
        try:
            # Get the layer's current style
            style_manager = QgsMapLayerStyleManager(layer)
            current_style = style_manager.currentStyle()

            # Get the fill color and stroke color from the style
            fill_color = current_style.symbol().color()
            stroke_color = current_style.symbol().strokeColor()

            # Print the fill color and stroke color
            print("Fill Color:", fill_color.name())
            print("Stroke Color:", stroke_color.name())
            return {"fill-color": fill_color.name() , "line-color": stroke_color.name()}
        except:
            return {}

    @staticmethod
    def symbol_to_layer_style(symbol):
        # Convert QgsSymbol to LayerStyle object
        # Extract fill and stroke colors
        # TODO: complete
        pass

    def generate_file_name(self, suffix):
        # Generate temporary file name using unique identifier
        temp_file = os.path.join(self.temp_dir, f"temp_{suffix}.tmp")
        return temp_file

    def export_raster_layer(self, layer: QgsVectorLayer):
        # Export vector layer to GeoPackage format
        # Set up export options, coordinate transformations
        # Use QgsVectorFileWriter to write layer data

        pass
    def export_vector_layer(self, layer):

        # Export raster layer to GeoTIFF format
        # Set up export options, coordinate transformations
        # Use QgsRasterFileWriter to write raster data

        dest_file = self.generate_file_name('.gpkg')
        writer_options = QgsVectorFileWriter.SaveVectorOptions()
        writer_options.driverName = 'GPKG'
        writer_options.layerName = 'parsed'
        writer_options.ct = QgsCoordinateTransform(
            layer.crs(),
            QgsCoordinateReferenceSystem('EPSG:4326'),
            self.transform_context
        ) 
        writer_options.forceMulti = True
        writer_options.overrideGeometryType = QgsWkbTypes.dropM(
            QgsWkbTypes.dropZ(layer.wkbType())
        )
        writer_options.includeZ = False
        writer_options.layerOptions = [
            'GEOMETRY_NAME=geom',
            'SPATIAL_INDEX=NO',
        ]

        # FID fields
        fields = layer.fields()
        fid_index = fields.lookupField('fid')
        writer_options.attributes = fields.allAttributesList()
        if fid_index >= 0:
            fid_type = fields.field(fid_index).type()
            if fid_type not in (QVariant.Int,
                                QVariant.UInt,
                                QVariant.LongLong,
                                QVariant.ULongLong):
                writer_options.attributes = [a for a in
                                             writer_options.attributes if
                                             a != fid_index]

        # pylint: disable=unused-variable
        res, error_message, new_filename, new_layer_name = QgsVectorFileWriter.writeAsVectorFormatV3(
                                                                                                    layer,
                                                                                                    dest_file,
                                                                                                    self.transform_context,
                                                                                                    writer_options,
                                                                                                    )

        if res not in (QgsVectorFileWriter.WriterError.NoError,
                QgsVectorFileWriter.WriterError.Canceled):
            raise LayerPackagingException(error_message)

        # layer_export_result = {
        #     QgsVectorFileWriter.WriterError.NoError:
        #         LayerExportResult.Success,
        #     QgsVectorFileWriter.WriterError.Canceled:
        #         LayerExportResult.Canceled,
        # }[res]



        # Validate result
        new_layer_uri = new_filename
        if new_layer_name:
            new_layer_uri += '|layername=' + new_layer_name
        res_layer = QgsVectorLayer(
            new_layer_uri, 'test', 'ogr'
        )
        if (layer.featureCount() > 0) and \
                res_layer.featureCount() != layer.featureCount():
            raise LayerPackagingException(
                self.tr(
                        'Packaged layer does not contain all features! '
                        '(has {}, expected {})').format(
                        res_layer.featureCount(), layer.featureCount())
                        )
        
        # Here the result should be returned 
        return {new_filename, dest_file}

    def __del__(self):
        # Clean up temporary files when the object is deleted
        for file in os.listdir(self.temp_dir):
            if file.startswith("temp_") and file.endswith(".tmp"):
                os.remove(os.path.join(self.temp_dir, file))
