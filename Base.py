import functools
import inspect

from .Exceptions import EmptyStartException, EdgeConditionException


## The finite state Node. This is what runs the code
class Node:

    ## Initialize the node
    # \param name the name of the function to run
    # \param out the out edges
    def __init__(self, name, out=None):
        self.out = out if out is not None else []
        self.name = name
        pass

    ## adds an out edge to the node
    # \param edge the edge to add this is an edge action
    def add_edge(self, edge):
        self.out.append(edge)
        pass

    ## Runs the action of the target passing in context and entities
    # \param target the target to run the function on
    # \param context the context of the machine. This could be manipulated at every node
    # \param entities the entities of the NLP result from wit.ai
    def run(self, target, context, entities):
        return getattr(target, self.name)(context, entities)

    ## Gets the next node
    # This runs the condition on the edge. If the edge.selectNext is not None,
    # this returns the next node
    def getNext(self, **kwargs):
        for edge in self.out:
            if edge.selectNext(**kwargs) is not None:
                return edge.end_node

## The edge class. This class is needed so that we can store conditions on the
# edge
class Edge:
    ## Initializes the class
    # \param start_node, the start node of the edge
    # \param end_node the end node of the edge
    # \param condition the condition used to traverse this node
    # \params entity_vars the properties on the entity needed to load
    def __init__(self, start_node, end_node, condition, entity_vars=None):
        self.start_node = start_node
        self.end_node = end_node
        self.entity_vars = entity_vars
        self.condition = compile(condition, "<Selector>", "eval")
        pass

    ## checks the edge condition to see if it is true
    # \param kwargs this is going to be anything we want to load into the eval
    #   function
    # \return self.end_node if condition is True else None
    def selectNext(self, **kwargs):
        locs = locals()
        locs.update(kwargs)
        if eval(self.condition, globals(), locs) :
            return self.end_node
        return None

    ## the decorator to mark a method as a node
    # \param edges a list of touples that are the condition and the start_node name
    # \usage
    # @Edge.Cond(edges=[("x==True", "start"), ("y==True", "next")])
    # \notes the name of the function is going to be the name of the node that
    @classmethod
    def Cond(cls, edges=None):
        def wrapper(func):
            func.__scond__ = edges
            return func
        return wrapper

## a function to check if this has the __scond__ attribute (aka marked be Edge.Cond)
# \param obj the object to inspect
def predicate(obj):
    return hasattr(obj, "__scond__")

## The metaclass for all of the Converse Bot
class ConverseMetaClass(type):

    ## Initializes the Class
    # \param name inherited from type
    # \param bases inherited from type
    # \param nmspc inherited from type
    # \notes this class is what iterates over all of the methods in a class and
    # is what loads the nodes and the edges of the FSM
    def __init__(cls, name, bases, nmspc):
        cls.start_node = Node("start")
        graph = dict()
        graph["start"] = cls.start_node
        for name, func in inspect.getmembers(cls, predicate=predicate):
            for edge in func.__scond__:
                start = graph.get(edge[1])
                if start is None:
                    start = Node(edge[1])
                    graph[edge[1]] = start
                    pass
                end = graph.get(name)
                if end is None:
                    end = Node(name)
                    graph[name] = end
                    pass
                edge = Edge(start, end, edge[0])
                start.add_edge(edge)
            pass
        return super(ConverseMetaClass, cls).__init__(name, bases, nmspc)

## the base class for all FSMs
class ConverseBase(object, metaclass=ConverseMetaClass):
    ## the start condition of the FSM (this is really a portion of the FSM)
    start_cond = None

    ## Initializes the class
    # \param entities the NLP entities
    def __init__(self, entities):
        self.entities = entities
        pass

    ## the start function (aka the start Node)
    # \param context the context of the run. Each node modifies this
    # \param entities the NLP entities
    # \notes every node method needs these same params
    def start(self, context,  entities):
        raise NotImplementedError

    ## gets the next Node in the FSM based on edge condition
    # \returns the next Node
    # \raises StopIteration if the current node is None
    def __next__(self):
        node = self.curNode
        if self.curNode != None:
            self.curNode = self.curNode.getNext(**self.entities)
            pass
        if node is None:
            raise StopIteration
        return node

    ## makes the class an iterator
    # \returns the object
    def __iter__(self):
        self.curNode = self.start_node
        return self

    ## The action to do when all the nodes are done
    # \param the resulting context
    # \returns this should return a string
    def finish(self, context):
        raise NotImplementedError

    ## runs the FSM given the current entity
    # \returns the value of finish
    def run(self):
        context = dict()
        for node in self:
            ret_val = node.run(target=self, context=context, entities=self.entities)
            context.update(ret_val)
            pass
        return self.finish(context)
    pass

class Brancher:
    def __init__(self, subclasses):
        self.subclasses = []
        for i in subclasses:
            if i.start_cond == None:
                raise EmptyStartException
            self.subclasses.append((i.start_cond))
        pass
    pass
