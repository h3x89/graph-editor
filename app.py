#! /usr/bin/python

import math
import os
# import copy

import networkx as nx

import pyglet
from pyglet.window import key
from pyglet.window import mouse
from pyglet.gl import *

__author__ = """\n""".join(['Robert Kubis (robert.h3x@gmail.com)'])

__all__ = ['write_graphml', 'read_graphml', 'generate_graphml',
           'GraphMLWriter', 'GraphMLReader']

class App(pyglet.window.Window):
    def __init__(self):
        super(App, self).__init__(800, 600, "Graph Editor", resizable=True)
        self.set_minimum_size(640, 480)

        self.g = nx.DiGraph()



        # check directed Graph - why not working???
        # default_edge_type='directed'
        # if self.g.is_directed():
        #         print "direct"



        self.mode = "node"
        self.selected = None
        self.offset = [0, 0]
        self.scale = 100.0
        # self.zoom_step = 0
        self.help = False
        self.info = False
        self.drag = False

        # create vertex list
        self.statusbar = pyglet.graphics.vertex_list(4,
            ('v2f', (0, 0, self.width, 0, self.width, 24, 0, 24)),
            ('c3B', (30, 30, 30) * 4)
        )
        self.line = pyglet.graphics.vertex_list(2,
            ('v2f', (self.width - 200, 2, self.width - 200, 22)),
            ('c3B', (80, 80, 80) * 2)
        )

        # labels
        self.cmd_label = pyglet.text.Label("Press 'h' for help", font_name='Sans', font_size=12, x=10, y=6)

        self.info_label = pyglet.text.Label("", multiline=True, x=50, y=self.height - 50,
            width=self.width-100, height=self.height-100, anchor_y="top", font_name="monospace", font_size=12)

        with open("help.txt") as help_file:
            self.help_label = pyglet.text.Label(help_file.read(), multiline=True, x=50, y=self.height - 50,
                    width=self.width-100, height=self.height-100, anchor_y="top", font_name="monospace", font_size=12)

        # I try draw circle but find simplest example :)
        # load images with anchor center of image (24x24)
        node_img = pyglet.resource.image("node.png")
        node_img.anchor_x = 12
        node_img.anchor_y = 12
        self.node_sprite = pyglet.sprite.Sprite(node_img)

        selected_img = pyglet.resource.image("node_selected.png")
        selected_img.anchor_x = 12
        selected_img.anchor_y = 12
        self.selected_sprite = pyglet.sprite.Sprite(selected_img)

    # MAGIC :D
    def check_node(self, x, y):
        x = x - self.offset[0]
        y = y - self.offset[1]

        for node in self.g.nodes_iter():
            d = (self.g.node[node]["x"] * self.scale - x)**2 + (self.g.node[node]["y"] * self.scale - y)**2
            # check minimal distance
            if d < 36:
                return node

        return False

    def check_edge(self, x, y):
        x = x - self.offset[0]
        y = y - self.offset[1]

        for edge in self.g.edges_iter():
            n1 = self.g.node[edge[0]]
            n2 = self.g.node[edge[1]]

            n1x = n1["x"] * self.scale
            n1y = n1["y"] * self.scale
            n2x = n2["x"] * self.scale
            n2y = n2["y"] * self.scale

            # circle containing the edge
            ccx = (n1x + n2x) / 2.0 # circle center x
            ccy = (n1y + n2y) / 2.0 # circle center y
            r = ((n1x - n2x)**2 + (n1y - n2y)**2) / 4.0 # squared radius

            # squared distance of the point (x, y) form the center of the circle above
            dp = (ccx - x)**2 + (ccy - y)**2

            if dp <= r:
                # more magic, don't touch!
                a = n2y - n1y
                b = n1x - n2x
                c = n2x * n1y - n1x * n2y

                d = abs(a * x + b * y + c) / math.sqrt(a**2 + b**2)

                if d < 5:
                    return edge

        return False

    def on_draw(self):
        self.clear()

        ox = self.offset[0]
        oy = self.offset[1]

        if self.help:
            # draw help on the screen
            self.help_label.draw()
        elif self.info:
            # draw info on the screen
            self.info_label.draw()
        else:
            # draw edges
            for edge in self.g.edges_iter():
                pyglet.gl.glColor3f(1, 0, 0)
                ### Make some magic and draw arrow
                pyglet.graphics.draw(2, pyglet.gl.GL_LINES, ('v2f', (
                    ox + self.g.node[edge[0]]["x"] * self.scale,
                    oy + self.g.node[edge[0]]["y"] * self.scale,
                    ox + self.g.node[edge[1]]["x"] * self.scale,
                    oy + self.g.node[edge[1]]["y"] * self.scale)))

            # draw nodes
            for node in self.g.nodes_iter():
                if node == self.selected:
                    self.selected_sprite.set_position(ox + self.g.node[node]["x"] * self.scale,
                            oy + self.g.node[node]["y"] * self.scale)
                    self.selected_sprite.draw()
                else:
                    self.node_sprite.set_position(ox + self.g.node[node]["x"] * self.scale,
                            oy + self.g.node[node]["y"] * self.scale)
                    self.node_sprite.draw()

            # draw statusbar
            self.statusbar.draw(pyglet.gl.GL_QUADS)
            self.line.draw(pyglet.gl.GL_LINES)

            # draw mode in the statusbar
            mode_label = pyglet.text.Label(self.mode, font_name='Sans', font_size=12, x=self.width - 190, y=6)
            mode_label.draw()

            # draw command
            self.cmd_label.draw()

            # if mode is modify, then show sidebar
            if self.mode == "modify":
                None
                # MAybe something for modify mode??

    def on_mouse_press(self, x, y, buttons, modifiers):
        node = self.check_node(x, y)
        # check if a node has not been clicked
        if node is not False:
            if self.mode == "modify":
                self.selected = node
        elif self.mode == "modify":
            self.selected = None

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):

        if buttons & mouse.LEFT and self.mode == "modify":
            if self.selected != None:
                node = self.g.node[self.selected]

                self.drag = True

                node["x"] += dx / self.scale
                node["y"] += dy / self.scale

    def on_mouse_release(self, x, y, buttons, modifiers):
        if buttons & mouse.LEFT:
            if self.mode == "node":
                node = self.check_node(x, y)
                # check if a node has not been clicked
                if node is False:
                    self.g.add_node(len(self.g), x=float(x - self.offset[0]) / self.scale, y=float(y - self.offset[1]) / self.scale)
                    self.selected = len(self.g) - 1
                else:
                    self.selected = node
            elif self.mode == "edge":
                node = self.check_node(x, y)
                # check if a node has been clicked
                if node is not False:
                    # if the node was already selected deselct it
                    if self.selected == node:
                        self.selected = None
                    # if no node was selected select the current one
                    elif self.selected == None:
                        self.selected = node
                    # if a different node is already selected add an edge between the two
                    # but check if there is already an edge between the two: in this case
                    # just do nothing
                    else:
                        if node not in self.g[self.selected]:
                            n1 = self.g.node[node]
                            n2 = self.g.node[self.selected]

                            n1x = n1["x"] * self.scale
                            n1y = n1["y"] * self.scale
                            n2x = n2["x"] * self.scale
                            n2y = n2["y"] * self.scale

                            d = math.sqrt((n1x - n2x)**2 + (n1y - n2y)**2)
                            self.g.add_edge(self.selected, node, weight=d)

                        self.selected = node
            elif self.mode == "delete":
                node = self.check_node(x, y)
                # check if a node has been clicked
                if node is not False:
                    # if the node was selected unselect it
                    if self.selected == node:
                        self.selected = None

                    # actually remove the node
                    self.g.remove_node(node)

                edge = self.check_edge(x, y)
                # check if an edge has been clicked
                if edge is not False:
                    # actually remove the edge
                    self.g.remove_edge(*edge)

        # dragging of node ended update some stuff
        if self.drag:
            node = self.g.node[self.selected]

            # change weight of connected edges
            for connected_node in iter(self.g[self.selected]):
                c_node = self.g.node[connected_node]
                # compute new distance
                d = math.sqrt((node["x"] - c_node["x"])**2 + (node["y"] - c_node["y"])**2)

                self.g[self.selected][connected_node]["weight"] = d

            self.drag = False

    def on_key_press(self, symbol, modifiers):
        if symbol == key.H:
            self.help = True
        elif symbol == key.I:
            self.info = True

            # get info
            node_number = len(self.g)
            edge_number = len(self.g.edges())

            self.info_label.text = "Info\n\nNumber of nodes: {0}\nNumber of edges: {1}".format(node_number, edge_number)

    def on_key_release(self, symbol, modifiers):
        if symbol == key.N:
            self.mode = "node"
        elif symbol == key.E:
            self.mode = "edge"
        elif symbol == key.D:
            self.mode = "delete"
        elif symbol == key.M:
            self.mode = "modify"
        elif symbol == key.S:
            nx.write_graphml(self.g, "graph.graphml")
            # get info about the file
            stat = os.stat("graph.graphml")
            num_nodes = len(self.g)
            # size in K
            size = stat.st_size / 1000.0
            # display info
            self.cmd_label.text = "{0} nodes written to graph.graphml ({1:,.1f}K)".format(num_nodes, size)
        elif symbol == key.L:
            try:
                self.g = nx.read_graphml("graph.graphml")
                # get info about the file
                stat = os.stat("graph.graphml")
                num_nodes = len(self.g)
                size = stat.st_size / 1000.0
                # display info
                self.cmd_label.text = "{0} nodes loaded from graph.graphml ({1:,.1f}K)".format(num_nodes, size)

                # clean up
                self.selected = None
            except IOError:
                # the file was missing
                self.cmd_label.text = "File graph.graphml not found"
        elif symbol == key.H:
            self.help = False
        elif symbol == key.I:
            self.info = False
        elif symbol == key.Q:
            self.close()
        elif symbol == key.ESCAPE:
            self.selected = None


if __name__ == "__main__":
    window = App()
    pyglet.app.run()
