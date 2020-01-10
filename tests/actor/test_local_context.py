
# import asyncio
# from queue import Queue
#
# import pytest
#
# from protoactor.actor.actor_context import RootContext
# from protoactor.actor.props import Props
#
# context = RootContext()
#
#
# @pytest.mark.asyncio
# async def test_reenter_after_can_do_action_for_task():
#     queue = Queue()
#
#     async def actor(ctx):
#         if ctx.message == 'hello1':
#             async def target():
#                 await asyncio.sleep(0.1)
#                 queue.put('bar')
#                 return 'hey1'
#
#             task = asyncio.ensure_future(target())
#
#             async def action():
#                 queue.put('baz')
#                 await ctx.respond(task.result())
#
#             ctx.reenter_after(task, action)
#         elif ctx.message == 'hello2':
#             queue.put('foo')
#             await ctx.respond('hey2')
#
#     props = Props.from_func(actor)
#     pid = context.spawn(props)
#
#     task1 = asyncio.ensure_future(context.request_future(pid, "hello1"))
#     task2 = asyncio.ensure_future(context.request_future(pid, "hello2"))
#
#     reply1 = await task1
#     reply2 = await task2
#
#     assert reply1 == 'hey1'
#     assert reply2 == 'hey2'
#
#     assert 'foo' == queue.get()
#     assert 'bar' == queue.get()
#     assert 'baz' == queue.get()
