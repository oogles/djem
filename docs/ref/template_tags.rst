=============
Template Tags
=============

Django Goodies provides several template tags as part of the ``goodies`` tag library.

.. _tags-ifperm:

``ifperm``
----------

The ``{% ifperm %}`` tag performs an object-level permission check, and if that check passes the contents of the block are output. To perform the permission check, it requires a ``User`` instance, the name of the permission and a model object. The check will pass if the given user has the given permission on the given model object.

.. code-block:: html+django
    
    {% load goodies %}
    ...
    {% ifperm user 'polls.vote_on_question' question_obj %}
        <a href="{% url 'vote' question_obj.pk %}">Vote Now</a>
    {% endifperm %}
    ...

The tag supports an ``else`` block, which will be output if the permissions check fails.

.. code-block:: html+django
    
    {% load goodies %}
    ...
    {% ifperm user 'polls.vote_on_question' question_obj %}
        <a href="{% url 'vote' question_obj.pk %}">Vote Now</a>
    {% else %}
        You do not have permission to vote on this question.
    {% endifperm %}
    ...

.. _tags-ifnotperm:

``ifnotperm``
-------------

The ``{% ifnotperm %}`` tag performs an object-level permission check, and if that check passes the contents of the block are output. To perform the permission check, it requires a ``User`` instance, the name of the permission and a model object. The check will pass if the given user *does not* have the given permission on the given model object.

.. code-block:: html+django
    
    {% load goodies %}
    ...
    {% ifnotperm user 'polls.vote_on_question' question_obj %}
        You do not have permission to vote on this question.
    {% endifnotperm %}
    ...

The tag supports an ``else`` block, which will be output if the permissions check fails.

.. code-block:: html+django
    
    {% load goodies %}
    ...
    {% ifnotperm user 'polls.vote_on_question' question_obj %}
        You do not have permission to vote on this question.
    {% else %}
        <a href="{% url 'vote' question_obj.pk %}">Vote Now</a>
    {% endifnotperm %}
    ...
