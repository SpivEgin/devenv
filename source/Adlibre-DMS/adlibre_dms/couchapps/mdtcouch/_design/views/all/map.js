function(doc) {
     if (doc.doc_type == "MetaDataTemplate")
          emit(doc._id, {rev:doc._rev});
}
