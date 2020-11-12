import random
import sys
from dataclasses import dataclass
from typing import Dict, List, Tuple, Union

random.seed("witch brews")

Ingredients = Tuple[int, int, int, int]


def log(x):
    print(x, file=sys.stderr, flush=True)


@dataclass(frozen=True)
class Action:
    action_id: int
    delta: Tuple[int, int, int, int]
    price: int


@dataclass(frozen=True)
class Brew(Action):
    pass


@dataclass(frozen=True)
class Spell(Action):
    castable: bool


class Rest:
    pass


@dataclass(frozen=True)
class Witch:
    inventory: Tuple[int, int, int, int]
    spells: Tuple[Spell]


def can_brew(inventory: Ingredients, target: Ingredients) -> bool:
    return all(i >= t for i, t in zip(inventory, target))


def add_inventories(x: Ingredients, y: Ingredients) -> Ingredients:
    result: Ingredients = tuple(map(lambda t: t[0] + t[1], zip(x, y)))  # type: ignore
    return result


def bfs_fastest_brew(
    start_witch: Witch, targets: List[Ingredients]
) -> List[Union[Rest, Spell]]:
    queue = [start_witch]
    prev = {start_witch: None}
    actions: Dict[Witch, Union[Rest, Spell]] = {start_witch: None}
    visited = {start_witch}
    while queue:
        cur = queue.pop(0)

        # break
        can_brew_something = any(can_brew(cur.inventory, t) for t in targets)
        if can_brew_something:
            result = []
            while cur is not None:
                action = actions[cur]
                if action is None:
                    break
                result.append(action)
                cur = prev[cur]
            return result

        # cast
        for i, spell in enumerate(cur.spells):
            if not spell.castable:
                continue
            new_spells = tuple(
                [
                    Spell(
                        action_id=s.action_id,
                        delta=s.delta,
                        castable=False
                        if spell.action_id == s.action_id
                        else s.castable,
                        price=s.price,
                    )
                    for s in cur.spells
                ]
            )
            new_witch = Witch(
                inventory=add_inventories(cur.inventory, spell.delta), spells=new_spells
            )
            if any(item < 0 for item in new_witch.inventory):
                continue
            if new_witch in visited:
                continue
            queue.append(new_witch)
            prev[new_witch] = cur
            actions[new_witch] = spell
            visited.add(new_witch)
        all_castable = []
        # rest
        all_castable = tuple(
            [
                Spell(
                    action_id=s.action_id,
                    delta=s.delta,
                    castable=True,
                    price=s.price,
                )
                for s in cur.spells
            ]
        )
        rested_witch = Witch(inventory=cur.inventory, spells=tuple(all_castable))
        if rested_witch not in visited:
            queue.append(rested_witch)
            prev[rested_witch] = cur
            actions[rested_witch] = Rest()
            visited.add(rested_witch)
    return []


def main() -> None:
    # game loop
    while True:
        orders: List[Brew] = []
        spells: List[Spell] = []

        action_count = int(input())  # the number of spells and recipes in play
        for i in range(action_count):
            # action_id: the unique ID of this spell or recipe
            # action_type: in the first league:
            #   BREW; later: CAST, OPPONENT_CAST, LEARN, BREW
            # delta_0: tier-0 ingredient change
            # delta_1: tier-1 ingredient change
            # delta_2: tier-2 ingredient change
            # delta_3: tier-3 ingredient change
            # price: the price in rupees if this is a potion
            # tome_index: in the first two leagues: always 0;
            #   later: the index in the tome if this is a tome spell,
            #   equal to the read-ahead tax
            # tax_count: in the first two leagues: always 0;
            #   later: the amount of taxed tier-0 ingredients you gain
            #   from learning this spell
            # castable: in the first league: always 0; later: 1
            #   if this is a castable player spell
            # repeatable: for the first two leagues: always 0; later: 1
            #   if this is a repeatable player spell
            (
                action_id,
                action_type,
                delta_0,
                delta_1,
                delta_2,
                delta_3,
                price,
                tome_index,
                tax_count,
                castable,
                repeatable,
            ) = input().split()
            action_id = int(action_id)
            delta_0 = int(delta_0)
            delta_1 = int(delta_1)
            delta_2 = int(delta_2)
            delta_3 = int(delta_3)
            price = int(price)
            tome_index = int(tome_index)
            tax_count = int(tax_count)
            castable = castable != "0"
            repeatable = repeatable != "0"

            if action_type == "BREW":
                orders.append(
                    Brew(
                        action_id=action_id,
                        delta=(delta_0, delta_1, delta_2, delta_3),
                        price=price,
                    )
                )
            elif action_type == "CAST":
                spells.append(
                    Spell(
                        action_id=action_id,
                        delta=(delta_0, delta_1, delta_2, delta_3),
                        price=price,
                        castable=castable,
                    )
                )

            # inv_0: tier-0 ingredients in inventory
            # score: amount of rupees
        *inventory, score = [int(j) for j in input().split()]
        _ = [int(j) for j in input().split()]  # other player

        # log(inventory)
        # log(spells)
        # log(orders)

        # in the first league: BREW <id>
        # | WAIT; later: BREW <id>
        # | CAST <id> [<times>]
        # | LEARN <id>
        # | REST
        # | WAIT
        max_price = 0
        max_ind = 0
        for i, a in enumerate(orders):
            remaining = (a + b for a, b in zip(inventory, a.delta))
            can_afford = all(x >= 0 for x in remaining)
            if can_afford and a.price > max_price:
                max_price = a.price
                max_ind = a.action_id

        if max_price > 0:
            print(f"BREW {max_ind}")
        else:
            targets = [tuple(-i for i in o.delta) for o in orders]
            result = bfs_fastest_brew(
                Witch(inventory=tuple(inventory), spells=tuple(spells)), targets=targets
            )
            if result:
                first = result[-1]
                if isinstance(first, Rest):
                    print("REST")
                else:
                    print(f"CAST {first.action_id}")
            else:
                print("REST")


if __name__ == "__main__":
    main()
