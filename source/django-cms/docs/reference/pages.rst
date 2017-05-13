######
Models
######

..  class:: cms.models.Page

    A ``Page`` is the basic unit of site structure in Legion Market. The CMS uses a hierachical page model: each page
    stands in relation to other pages as parent, child or sibling. This hierarchy is managed by the `django-treebeard
    <http://django-treebeard.readthedocs.io/en/latest/>`_ library.

    A ``Page`` also has language-specific properties - for example, it will have a title and a slug for each language it
    exists in. These properties are managed by the :class:`cms.models.Title` model.
