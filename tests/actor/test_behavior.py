import pytest

from protoactor.actor.actor import RootContext, Actor
from protoactor.actor.behavior import Behavior
from protoactor.actor.props import Props


class PressSwitch:
    pass


class Touch:
    pass


class HitWithHammer:
    pass


class LightBulb(Actor):
    def __init__(self):
        self._smashed = False
        self._behavior = Behavior()
        self._behavior.become(self.off)

    async def off(self, context):
        if isinstance(context.message, PressSwitch):
            await context.respond("Turning on")
            self._behavior.become(self.on)
        elif isinstance(context.message, Touch):
            await context.respond("Cold")

    async def on(self, context):
        if isinstance(context.message, PressSwitch):
            await context.respond("Turning off")
            self._behavior.become(self.off)
        elif isinstance(context.message, Touch):
            await context.respond("Hot!")

    async def receive(self, context):
        if isinstance(context.message, HitWithHammer):
            await context.respond("Smashed!")
            self._smashed = True
        elif isinstance(context.message, PressSwitch) and self._smashed:
            await context.respond("Broken")
        elif isinstance(context.message, Touch) and self._smashed:
            await context.respond("OW!")

        await self._behavior.receive_async(context)


@pytest.mark.asyncio
async def test_can_change_states():
    test_actor_props = Props.from_producer(LightBulb)
    context = RootContext()
    actor = context.spawn(test_actor_props)
    assert await context.request_async(actor, PressSwitch()) == "Turning on"
    assert await context.request_async(actor, Touch())== "Hot!"
    assert await context.request_async(actor, PressSwitch()) == "Turning off"
    assert await context.request_async(actor, Touch()) == "Cold"


@pytest.mark.asyncio
async def test_can_use_global_behaviour():
    context = RootContext()
    test_actor_props = Props.from_producer(LightBulb)
    actor = context.spawn(test_actor_props)
    _ = await context.request_async(actor, PressSwitch())
    assert await context.request_async(actor, HitWithHammer()) == "Smashed!"
    assert await context.request_async(actor, PressSwitch()) == "Broken"
    assert await context.request_async(actor, Touch()) == "OW!"


@pytest.mark.asyncio
async def test_pop_behavior_should_restore_pushed_behavior():
    behavior = Behavior()

    async def func_1(ctx):
        if isinstance(ctx.message, str):
            async def func_2(ctx2):
                await ctx2.respond(42)
                behavior.unbecome_stacked()

            behavior.become_stacked(func_2)
            await ctx.respond(ctx.message)

    behavior.become(func_1)

    props = Props.from_func(behavior.receive_async)
    context = RootContext()
    pid = context.spawn(props)

    reply = await context.request_async(pid, "number")
    reply_after_push = await context.request_async(pid, None)
    reply_after_pop = await context.request_async(pid, "answertolifetheuniverseandeverything")

    assert reply + str(reply_after_push) + reply_after_pop == "number42answertolifetheuniverseandeverything"
