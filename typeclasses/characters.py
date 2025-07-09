"""
Characters

Characters are (by default) Objects setup to be puppeted by Accounts.
They are what you "see" in game. The Character class in this module
is setup to be the "default" character type created by the default
creation commands.

"""


from evennia.contrib.game_systems.cooldowns import CooldownHandler
from evennia.objects.objects import DefaultCharacter
from evennia.typeclasses.attributes import NAttributeProperty
from evennia.utils.evform import EvForm
from evennia.utils.evtable import EvTable
from evennia.utils.logger import log_trace
from evennia.utils.utils import lazy_property
from world import rules
from world.buffs import AbstractBuffHandler
from world.characters.classes import CharacterClasses, CharacterClass
from world.characters.races import Races, Race

from world.equipment import EquipmentError, EquipmentHandler
from world.levelling import LevelsHandler
from world.quests import QuestHandler
from .objects import ObjectParent

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from world.combat import CombatHandler


# from world.utils import get_obj_stats


class BaseCharacter(ObjectParent, DefaultCharacter):
    is_pc = False

    def at_object_creation(self):
        super().at_object_creation()
        self.db.hp = 1
        self.db.hp_max = 1
        self.db.mana = 1
        self.db.mana_max = 1
        self.db.stamina = 1
        self.db.stamina_max = 1
        self.db.strength = 1
        self.db.will = 1
        self.db.cunning = 1
        self.db.cclass_key = None
        self.db.race_key = None
        self.db.aggro = "n"  # Defensive, Normal, or Aggressive (d/n/a)
    
    # Character stats properties
    @property
    def hp(self):
        return self.db.hp or 1
    
    @hp.setter
    def hp(self, value):
        self.db.hp = value
    
    @property
    def hp_max(self):
        return self.db.hp_max or 1
    
    @hp_max.setter
    def hp_max(self, value):
        self.db.hp_max = value
    
    @property
    def mana(self):
        return self.db.mana or 1
    
    @mana.setter
    def mana(self, value):
        self.db.mana = value
    
    @property
    def mana_max(self):
        return self.db.mana_max or 1
    
    @mana_max.setter
    def mana_max(self, value):
        self.db.mana_max = value
    
    @property
    def stamina(self):
        return self.db.stamina or 1
    
    @stamina.setter
    def stamina(self, value):
        self.db.stamina = value
    
    @property
    def stamina_max(self):
        return self.db.stamina_max or 1
    
    @stamina_max.setter
    def stamina_max(self, value):
        self.db.stamina_max = value
    
    @property
    def strength(self):
        return self.db.strength or 1
    
    @strength.setter
    def strength(self, value):
        self.db.strength = value
    
    @property
    def will(self):
        return self.db.will or 1
    
    @will.setter
    def will(self, value):
        self.db.will = value
    
    @property
    def cunning(self):
        return self.db.cunning or 1
    
    @cunning.setter
    def cunning(self, value):
        self.db.cunning = value
    
    @property
    def cclass_key(self):
        return self.db.cclass_key
    
    @cclass_key.setter
    def cclass_key(self, value):
        self.db.cclass_key = value
    
    @property
    def race_key(self):
        return self.db.race_key
    
    @race_key.setter
    def race_key(self, value):
        self.db.race_key = value
    
    @property
    def aggro(self):
        return self.db.aggro or "n"
    
    @aggro.setter
    def aggro(self, value):
        self.db.aggro = value

    @property
    def cclass(self) -> CharacterClass | None:
        cclass = self.ndb.cclass
        if cclass is None:
            cclass = CharacterClasses.get(self.db.cclass_key)
            self.ndb.cclass = cclass

        return cclass

    @property
    def combat(self) -> 'CombatHandler | None':
        return self.ndb.combat

    @combat.setter
    def combat(self, value) -> None:
        self.ndb.combat = value


    @property
    def race(self) -> Race:
        race = self.ndb.race
        if race is None:
            race = Races.get(self.db.race_key)
            self.ndb.race = race

        return race

    @lazy_property
    def cooldowns(self):
        return CooldownHandler(self)

    @property
    def hurt_level(self):
        """
        String describing how hurt this character is.
        """
        percent = max(0, min(100, 100 * (self.hp / self.hp_max)))
        if 95 < percent <= 100:
            return "|gPerfect|n"
        elif 80 < percent <= 95:
            return "|gScraped|n"
        elif 60 < percent <= 80:
            return "|GBruised|n"
        elif 45 < percent <= 60:
            return "|yHurt|n"
        elif 30 < percent <= 45:
            return "|yWounded|n"
        elif 15 < percent <= 30:
            return "|rBadly wounded|n"
        elif 1 < percent <= 15:
            return "|rBarely hanging on|n"
        elif percent == 0:
            return "|RCollapsed!|n"

    def heal(self, hp, healer=None):
        """
        Heal by a certain amount of HP.

        """
        damage = self.hp_max - self.hp
        healed = min(damage, hp)
        self.hp += healed

        if healer is self:
            self.msg(f"|gYou heal yourself for {healed} health.|n")
        elif healer:
            self.msg(f"|g{healer.key} heals you for {healed} health.|n")
        else:
            self.msg(f"You are healed for {healed} health.")

    @lazy_property
    def equipment(self):
        """Allows to access equipment like char.equipment.worn"""
        return EquipmentHandler(self)

    @property
    def weapon(self):
        return self.equipment.weapon

    @property
    def armor(self):
        return self.equipment.armor

    @property
    def shield(self):
        return self.equipment.shield

    @lazy_property
    def levels(self):
        """Allows to access equipment like char.equipment.worn"""
        return LevelsHandler(self)

    @lazy_property
    def buffs(self):
        # TODO Implement
        return AbstractBuffHandler()

    def at_damage(self, damage, attacker=None):
        """
        Called when attacked and taking damage.

        """
        self.hp -= damage
        if self.hp <= 0:
            self.at_defeat()

    def spend_stamina(self, amount):
        """
        Called when attacking and defending
        """
        self.stamina -= amount

    def spend_mana(self, amount):
        """
        Called when casting spells
        """
        self.mana -= amount

    def at_recovery(self):
        """
        Called periodically by the combat ticker

        """
        self.stamina += self.strength
        if self.stamina > self.stamina_max:
            self.stamina = self.stamina_max

        self.mana += self.will
        if self.mana > self.mana_max:
            self.mana = self.mana_max

    def at_defeat(self):
        """
        Called when this living thing reaches HP 0.

        """
        # by default, defeat means death
        self.at_death()

    def at_death(self):
        """
        Called when this living thing dies.

        """
        if self.combat:
            self.combat.remove(self)

        self.location.msg_contents(f"$You() $conj(die).", from_obj=self)

    def at_pay(self, amount):
        """
        Get coins, but no more than we actually have.

        """
        amount = min(amount, self.coins)
        self.coins -= amount
        return amount

    def at_looted(self, looter):
        """
        Called when being looted (after defeat).

        Args:
            looter (Object): The one doing the looting.

        """
        max_steal = rules.dice.roll("1d10")
        stolen = self.at_pay(max_steal)

        looter.coins += stolen

        self.location.msg_contents(
            f"$You(looter) loots $You() for {stolen} coins!",
            from_obj=self,
            mapping={"looter": looter},
        )

    def pre_loot(self, defeated_enemy):
        """
        Called just before looting an enemy.

        Args:
            defeated_enemy (Object): The enemy soon to loot.

        Returns:
            bool: If False, no looting is allowed.

        """
        pass

    def at_do_loot(self, defeated_enemy):
        """
        Called when looting another entity.

        Args:
            defeated_enemy: The thing to loot.

        """
        defeated_enemy.at_looted(self)

    def post_loot(self, defeated_enemy):
        """
        Called just after having looted an enemy.

        Args:
            defeated_enemy (Object): The enemy just looted.

        """
        pass


class Character(BaseCharacter):
    """
    The Character typeclass for the game. This is the default typeclass new player
    characters are created as, so the EvAdventure player character is appropriate here.
    """

    is_pc = True

    def at_object_creation(self):
        super().at_object_creation()
        self.db.hp = 10
        self.db.hp_max = 10
        self.db.mana = 10
        self.db.mana_max = 10
        self.db.stamina = 4
        self.db.stamina_max = 4
        self.db.coins = 0  # copper coins

    # Combat State Tracking

    adelay = NAttributeProperty( default=0.0 ) # delay attacks until float time
    mdelay = NAttributeProperty( default=0.0 ) # delay movement until float time
    
    @property
    def coins(self):
        return self.db.coins or 0
    
    @coins.setter
    def coins(self, value):
        self.db.coins = value


    @lazy_property
    def quests(self):
        """Access and track quests"""
        return QuestHandler(self)



    def at_pre_object_receive(self, moved_object, source_location, **kwargs):
        """
        Hook called by Evennia before moving an object here. Return False to abort move.

        Args:
            moved_object (Object): Object to move into this one (that is, into inventory).
            source_location (Object): Source location moved from.
            **kwargs: Passed from move operation; the `move_type` is useful; if someone is giving
                us something (`move_type=='give'`) we want to ask first.

        Returns:
            bool: If move should be allowed or not.

        """
        # this will raise EquipmentError if inventory is full
        return self.equipment.validate_slot_usage(moved_object)

    def at_object_receive(self, moved_object, source_location, **kwargs):
        """
        Hook called by Evennia as an object is moved here. We make sure it's added
        to the equipment handler.

        Args:
            moved_object (Object): Object to move into this one (that is, into inventory).
            source_location (Object): Source location moved from.
            **kwargs: Passed from move operation; unused here.

        """
        try:
            self.equipment.add(moved_object)
        except EquipmentError as err:
            log_trace(f"at_object_receive error: {err}")

    def at_pre_object_leave(self, leaving_object, destination, **kwargs):
        """
        Hook called when dropping an item. We don't allow to drop weilded/worn items
        (need to unwield/remove them first). Return False to

        """
        return True

    def at_object_leave(self, moved_object, destination, **kwargs):
        """
        Called just before an object leaves from inside this object

        Args:
            moved_obj (Object): The object leaving
            destination (Object): Where `moved_obj` is going.
            **kwargs (dict): Arbitrary, optional arguments for users
                overriding the call (unused by default).

        """
        self.equipment.remove(moved_object)

    def at_defeat(self):
        """
        This happens when character drops <= 0 HP. For Characters, this means rolling on
        the death table.

        """
        if self.location.allow_death:
            rules.dice.roll_death(self)
        else:
            self.location.msg_contents(
                "|y$You() $conj(yield), beaten and out of the fight.|n"
            )
            self.hp = self.hp_max

    def at_death(self):
        """
        Called when character dies.

        """
        self.location.msg_contents(
            "|r$You() $conj(collapse) in a heap.\nDeath embraces you ...|n",
            from_obj=self,
        )

    def at_pre_loot(self):
        """
        Called before allowing to loot. Return False to block enemy looting.
        """
        # don't allow looting in pvp
        return not self.location.allow_pvp

    def at_looted(self, looter):
        """
        Called when being looted.

        """
        pass

    def at_post_puppet(self, **kwargs):
        super().at_post_puppet(**kwargs)
        # Here we add Keybinds for Evelite Webclient so we can walk around with the numpad
        self.msg(
            key_cmds=(
                '', {
                    '7': 'northwest',
                    '8': 'north',
                    '9': 'northeast',
                    '1': 'southwest',
                    '2': 'south',
                    '3': 'southeast',
                    '4': 'west',
                    '6': 'east',
                    '5': 'look',
                }
            )
        )

    def at_post_move(self, source_location, **kwargs):
        super().at_post_move(source_location, **kwargs)
        if map_getter := getattr(self.location, 'get_map_display', None):
            # Send the map to the WebClient
            self.msg(map=map_getter(looker=self))



# character sheet visualization

_SHEET = """
 +----------------------------------------------------------------------------+
 | Name: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx1xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx |
 +----------------------------------------------------------------------------+
 | STR: x2xxxxx  DEX: x3xxxxx  CON: x4xxxxx  WIS: x5xxxxx  CHA: x6xxxxx       |
 +----------------------------------------------------------------------------+
 | HP: x7xxxxx                                      XP: x8xxxxx  Level: x9x   |
 +----------------------------------------------------------------------------+
 | Desc: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx |
 | xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxBxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx |
 | xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx |
 +----------------------------------------------------------------------------+
 | cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc |
 | cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc |
 | cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc |
 | cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc |
 | cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc |
 | cccccccccccccccccccccccccccccccccc1ccccccccccccccccccccccccccccccccccccccc |
 | cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc |
 | cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc |
 | cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc |
 | cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc |
 | cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc |
 | cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc |
 | cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc |
 +----------------------------------------------------------------------------+
    """


def get_character_sheet(character):
    """
    Generate a character sheet. This is grouped in a class in order to make
    it easier to override the look of the sheet.

                TODO: This is NOT a class - figure out how this is intended to be used and accessed

    """

    @staticmethod
    def get(character):
        """
        Generate a character sheet from the character's stats.

        """
        equipment = character.equipment.all()
        # divide into chunks of max 10 length (to go into two columns)
        equipment_table = EvTable(
            table=[equipment[i : i + 10] for i in range(0, len(equipment), 10)]
        )
        form = EvForm({"FORMCHAR": "x", "TABLECHAR": "c", "SHEET": _SHEET})
        form.map(
            cells={
                1: character.key,
                2: f"+{character.strength}({character.strength + 10})",
                3: f"+{character.dexterity}({character.dexterity + 10})",
                4: f"+{character.constitution}({character.constitution + 10})",
                5: f"+{character.wisdom}({character.wisdom + 10})",
                6: f"+{character.charisma}({character.charisma + 10})",
                7: f"{character.hp}/{character.hp_max}",
                8: character.xp,
                9: character.level,
                "A": character.db.desc,
            },
            tables={
                1: equipment_table,
            },
        )
        return str(form)
