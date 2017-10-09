=============
Template Tags
=============

Djem provides several template tags as part of the ``djem`` tag library.

.. _tags-ifperm:

``ifperm``
----------

The ``{% ifperm %}`` block tag performs an object-level permission check and, if that check *passes*, renders contents of the block. To perform the permission check, it requires a ``User`` instance, the name of the permission and a model instance. The check will pass if the given user has the given permission on the given instance.

.. code-block:: html+django

    {% load djem %}
    ...
    {% ifperm user 'polls.vote_on_question' question_obj %}
        <a href="{% url 'vote' question_obj.pk %}">Vote Now</a>
    {% endifperm %}
    ...

The tag supports an ``else`` block, which will be rendered if the user does not have permission.

.. code-block:: html+django

    {% load djem %}
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

The ``{% ifnotperm %}`` block tag performs an object-level permission check and, if that check *fails*, the contents of the block are rendered. To perform the permission check, it requires a ``User`` instance, the name of the permission and a model instance. The check will fail if the given user *does not* have the given permission on the given instance.

.. code-block:: html+django

    {% load djem %}
    ...
    {% ifnotperm user 'polls.vote_on_question' question_obj %}
        You do not have permission to vote on this question.
    {% endifnotperm %}
    ...

The tag supports an ``else`` block, which will be rendered if the user does have permission.

.. code-block:: html+django

    {% load djem %}
    ...
    {% ifnotperm user 'polls.vote_on_question' question_obj %}
        You do not have permission to vote on this question.
    {% else %}
        <a href="{% url 'vote' question_obj.pk %}">Vote Now</a>
    {% endifnotperm %}
    ...
