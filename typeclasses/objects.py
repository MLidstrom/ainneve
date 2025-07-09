"""
Object

The Object is the base class for things in the game world.

Note that the default Character, Room and Exit do not inherit from Object,
but do inherit from the provided mixin ObjectParent by default.

"""
from evennia.objects.objects import DefaultObject
from evennia.utils.utils import make_iter

from world.enums import Ability, CombatRange, ObjType, WieldLocation, AttackType
from world.utils import get_obj_stats


class ObjectParent:
    """
    This is a mixin that can be used to override *all* entities inheriting at
    some distance from DefaultObject (Objects, Exits, Characters and Rooms).

    Just add any method that exists on `DefaultObject` to this class. If one
    of the derived classes has itself defined that same hook already, that will
    take precedence.

    """


class Object(ObjectParent, DefaultObject):
    """
    Base in-game entity.

    """

    def at_object_creation(self):
        # inventory management
        self.db.inventory_use_slot = WieldLocation.BACKPACK
        # how many inventory slots it uses (can be a fraction)
        self.db.size = 1
        self.db.value = 0
        
        # Set up object types
        for obj_type in make_iter(self.obj_type):
            self.tags.add(obj_type.value, category="obj_type")
    
    @property
    def inventory_use_slot(self):
        return self.db.inventory_use_slot or WieldLocation.BACKPACK
    
    @inventory_use_slot.setter
    def inventory_use_slot(self, value):
        self.db.inventory_use_slot = value
    
    @property
    def size(self):
        return self.db.size or 1
    
    @size.setter
    def size(self, value):
        self.db.size = value
    
    @property
    def value(self):
        return self.db.value or 0
    
    @value.setter
    def value(self, value):
        self.db.value = value

    # can also be an iterable, for adding multiple obj-type tags
    obj_type = ObjType.GEAR

    def get_display_header(self, looker, **kwargs):
        return ""  # this is handled by get_obj_stats

    def get_display_desc(self, looker, **kwargs):
        return get_obj_stats(self, owner=looker)

    def has_obj_type(self, objtype):
        """
        Check if object is of a particular type.

        typeobj_enum (enum.ObjType): A type to check, like enums.TypeObj.TREASURE.

        """
        return objtype.value in make_iter(self.obj_type)

    def get_help(self):
        """
        Get help text for the item.

        Returns:
            str: The help text, by default taken from the `.help_text` property.

        """
        return "No help for this item."


class ObjectFiller(Object):
    """
    In _Knave_, the inventory slots act as an extra measure of how you are affected by
    various averse effects. For example, mud or water could fill up some of your inventory
    slots and make the equipment there unusable until you cleaned it. Inventory is also
    used to track how long you can stay under water etc - the fewer empty slots you have,
    the less time you can stay under water due to carrying so much stuff with you.

    This class represents such an effect filling up an empty slot. It has a quality of 0,
    meaning it's unusable.

    """

    obj_type = ObjType.QUEST.value  # can't be sold
    
    def at_object_creation(self):
        super().at_object_creation()
        self.db.quality = 0
    
    @property
    def quality(self):
        return self.db.quality or 0
    
    @quality.setter
    def quality(self, value):
        self.db.quality = value


class QuestObject(Object):
    """
    A quest object. These cannot be sold and only be used for quest resolution.

    """

    obj_type = ObjType.QUEST
    
    def at_object_creation(self):
        super().at_object_creation()
        self.db.value = 0


class TreasureObject(Object):
    """
    A 'treasure' is mainly useful to sell for coin.

    """

    obj_type = ObjType.TREASURE
    
    def at_object_creation(self):
        super().at_object_creation()
        self.db.value = 100


class ConsumableObject(Object):
    """
    Item that can be 'used up', like a potion or food. Weapons, armor etc does not
    have a limited usage in this way.

    """

    obj_type = ObjType.CONSUMABLE
    
    def at_object_creation(self):
        super().at_object_creation()
        self.db.size = 0.25
        self.db.uses = 1
    
    @property
    def uses(self):
        return self.db.uses or 1
    
    @uses.setter
    def uses(self, value):
        self.db.uses = value

    def at_use(self, user, *args, **kwargs):
        """
        Consume a 'use' of this item. Once it reaches 0 uses, it should normally
        not be usable anymore and probably be deleted.

        Args:
            user (Object): The one using the item.
            *args, **kwargs: Extra arguments depending on the usage and item.

        """
        pass

    def at_post_use(self, user, *args, **kwargs):
        """
        Called after this item was used.

        Args:
            user (Object): The one using the item.
            *args, **kwargs: Optional arguments.

        """
        self.uses -= 1
        if self.uses <= 0:
            user.msg(f"{self.key} was used up.")
            self.delete()


class WeaponObject(Object):
    """
    Base weapon class for all  weapons.

    """

    obj_type = ObjType.WEAPON
    
    def at_object_creation(self):
        super().at_object_creation()
        self.db.inventory_use_slot = WieldLocation.WEAPON_HAND
        self.db.quality = 3
        self.db.attack_range = CombatRange.MELEE
        self.db.attack_type = AttackType.MELEE
        self.db.defense_type = Ability.ARMOR
        self.db.min_damage = 1
        self.db.max_damage = 4
        self.db.stamina_cost = 2
        self.db.cooldown = 2
    
    @property
    def quality(self):
        return self.db.quality or 3
    
    @quality.setter
    def quality(self, value):
        self.db.quality = value
    
    @property
    def attack_range(self):
        return self.db.attack_range or CombatRange.MELEE
    
    @attack_range.setter
    def attack_range(self, value):
        self.db.attack_range = value
    
    @property
    def attack_type(self):
        return self.db.attack_type or AttackType.MELEE
    
    @attack_type.setter
    def attack_type(self, value):
        self.db.attack_type = value
    
    @property
    def defense_type(self):
        return self.db.defense_type or Ability.ARMOR
    
    @defense_type.setter
    def defense_type(self, value):
        self.db.defense_type = value
    
    @property
    def min_damage(self):
        return self.db.min_damage or 1
    
    @min_damage.setter
    def min_damage(self, value):
        self.db.min_damage = value
    
    @property
    def max_damage(self):
        return self.db.max_damage or 4
    
    @max_damage.setter
    def max_damage(self, value):
        self.db.max_damage = value
    
    @property
    def stamina_cost(self):
        return self.db.stamina_cost or 2
    
    @stamina_cost.setter
    def stamina_cost(self, value):
        self.db.stamina_cost = value
    
    @property
    def cooldown(self):
        return self.db.cooldown or 2
    
    @cooldown.setter
    def cooldown(self, value):
        self.db.cooldown = value


class Runestone(WeaponObject, ConsumableObject):
    """
    Base class for magic runestones. In _Knave_, every spell is represented by a rune stone
    that takes up an inventory slot. It is wielded as a weapon in order to create the specific
    magical effect provided by the stone. Normally each stone can only be used once per day but
    they are quite powerful (and scales with caster level).

    """

    obj_type = (ObjType.WEAPON, ObjType.MAGIC)
    
    def at_object_creation(self):
        super().at_object_creation()
        self.db.inventory_use_slot = WieldLocation.TWO_HANDS
        self.db.quality = 3
        self.db.attack_type = Ability.WIL
        self.db.defense_type = Ability.CUN
        self.db.damage_roll = "1d8"
    
    @property
    def damage_roll(self):
        return self.db.damage_roll or "1d8"
    
    @damage_roll.setter
    def damage_roll(self, value):
        self.db.damage_roll = value

    def at_post_use(self, user, *args, **kwargs):
        """Called after the spell was cast"""
        self.uses -= 1
        # the rune stone is not deleted after use, but
        # it needs to be refreshed after resting.

    def refresh(self):
        self.uses = 1


class ArmorObject(Object):
    """
    Base class for all wearable Armors.

    """

    obj_type = ObjType.ARMOR
    
    def at_object_creation(self):
        super().at_object_creation()
        self.db.inventory_use_slot = WieldLocation.BODY
        self.db.armor = 1
        self.db.quality = 3
    
    @property
    def armor(self):
        return self.db.armor or 1
    
    @armor.setter
    def armor(self, value):
        self.db.armor = value
    
    @property
    def quality(self):
        return self.db.quality or 3
    
    @quality.setter
    def quality(self, value):
        self.db.quality = value


class Shield(ArmorObject):
    """
    Base class for all Shields.

    """

    obj_type = ObjType.SHIELD
    
    def at_object_creation(self):
        super().at_object_creation()
        self.db.inventory_use_slot = WieldLocation.SHIELD_HAND


class Helmet(ArmorObject):
    """
    Base class for all Helmets.

    """

    obj_type = ObjType.HELMET
    
    def at_object_creation(self):
        super().at_object_creation()
        self.db.inventory_use_slot = WieldLocation.HEAD
