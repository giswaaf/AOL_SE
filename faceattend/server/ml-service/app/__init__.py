# Patch google.protobuf to prevent 'MessageFactory' and 'SymbolDatabase' objects having no attribute 'GetPrototype'
# which happens when using newer protobuf version with libraries like mediapipe/tensorflow.
try:
    import google._upb._message
    if not hasattr(google._upb._message.FieldDescriptor, "label"):
        @property
        def get_label(self):
            if self.is_repeated:
                return 3 # LABEL_REPEATED
            elif self.is_required:
                return 2 # LABEL_REQUIRED
            else:
                return 1 # LABEL_OPTIONAL
        google._upb._message.FieldDescriptor.label = get_label
except Exception:
    pass
try:
    import google.protobuf.message_factory

    if not hasattr(google.protobuf.message_factory.MessageFactory, "GetPrototype"):
        def get_prototype_patch(self, descriptor):
            return google.protobuf.message_factory.GetMessageClass(descriptor)
        google.protobuf.message_factory.MessageFactory.GetPrototype = get_prototype_patch
except ImportError:
    pass

try:
    import google.protobuf.symbol_database
    import google.protobuf.message_factory

    if not hasattr(google.protobuf.symbol_database.SymbolDatabase, "GetPrototype"):
        def get_prototype_patch(self, descriptor):
            return google.protobuf.message_factory.GetMessageClass(descriptor)
        google.protobuf.symbol_database.SymbolDatabase.GetPrototype = get_prototype_patch
except ImportError:
    pass
