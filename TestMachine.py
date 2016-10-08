from .Base import ConverseBase, Edge

class Test(ConverseBase):

    def start(self, context,  entities):
        print ("Starting")
        context["count"] = 1
        return context

    @Edge.Cond(edges=[("x['thing']==1", "start")])
    def second(self, context, entities):
        print("second")
        context["count"] += 1
        return context

    @Edge.Cond(edges=[("x.get('thing2')==10000", "second")])
    def never(self, context, entities):
        print("I shouldn't be here =(")
        context["count"] -= 1
        return context

    @Edge.Cond(edges=[("x.get('this') is not None", "second")])
    def fourth(self, context, entities):
        print("awesome")
        context["count"] += 1
        return context

    @Edge.Cond(edges=[("x.get('this') is None", "second")])
    def fifth(self, context, entities):
        print("This is an alternate path")
        context["count"] += 10
        return context

    def finish(self, context):
        print("This is done with context:", context)
        return "YESSSSSSS"

entities = dict(x=dict(thing=1, thing2="10000"))
tst = Test(entities)
tst.run()
