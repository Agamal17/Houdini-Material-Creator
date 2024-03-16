import os
import re
from PySide2.QtWidgets import *
from PySide2.QtCore import Qt


class App(QDialog):
    def __init__(self):
        super(App, self).__init__()
        self.setWindowTitle("Texture Generator")
        self.resize(400, 300)
        self.folder = None
        self.node = None

        self.lyt = QVBoxLayout()
        self.setLayout(self.lyt)

        self.uplyt = QHBoxLayout()
        self.b1 = QPushButton("Choose Textures Path")
        self.b1.clicked.connect(self.txtpath)
        self.l1 = QLabel()
        self.midlyt = QHBoxLayout()
        self.b2 = QPushButton("Select Material Library Path")
        self.b2.clicked.connect(self.libpath)
        self.l2 = QLabel()
        self.b = QPushButton("Generate")
        self.b.clicked.connect(lambda: create_material(self.folder, self.node))

        self.uplyt.addWidget(self.b1)
        self.uplyt.addWidget(self.l1)
        self.midlyt.addWidget(self.b2)
        self.midlyt.addWidget(self.l2)
        self.lyt.addLayout(self.uplyt)
        self.lyt.addLayout(self.midlyt)
        self.lyt.addWidget(self.b)

        self.setParent(hou.ui.mainQtWindow(), Qt.Window)

    def txtpath(self):
        self.folder = QFileDialog.getExistingDirectory(caption='Select a folder')
        self.l1.setText(self.folder)

    def libpath(self):
        res = hou.selectedNodes()[0]
        self.node = res
        self.l2.setText(self.node.name())


class mtlx:
    def __init__(self, map=None, file=''):
        self.maptype = map
        self.file = file

    def list_mtlx(self, folder):
        asset_names = set()
        material_files = []
        assets = {}

        for root, _, file in os.walk(folder):
            for i in range(len(file)):
                material_files.append(os.path.join(root, file[i]))

        for _asset in material_files:
            filename = _asset.split('/')[-1]
            filename = filename.split('\\')[-1]
            if 'basecolor' in filename.lower():
                asset = re.split('_basecolor_', filename, flags=re.IGNORECASE)[0]
                asset_names.add(asset)

        for asset in asset_names:
            assets[asset] = []

        for asset in asset_names:
            for file in material_files:
                if asset in file:
                    map = file.split('/')[-1].split(asset + '_')[-1].split('_')[0]
                    assets[asset].append(mtlx(map, file))
        # print(assets['b_04_Ground'][0].maptype, assets['b_04_Ground'][0].path)

        return assets


def create_material(folder, node):
    hip = hou.expandString("$HIP")
    parent = node
    type_dic = {'base_color': ['basecolor', 'color', 'base', 'albedo'], 'height': ['height'], 'metalness': ['metallic'],
                'normal': ['normal'], 'specular_roughness': ['roughness']}

    mat = mtlx()
    assets = mat.list_mtlx(folder)
    for asset, materials in assets.items():
        std = hou.node(parent.path()).createNode('mtlxstandard_surface', asset)
        for i in range(len(materials)):
            mtlxnode = hou.node(parent.path()).createNode('mtlximage', asset + '_' + materials[i].maptype)
            if hip in materials[i].path:
                path = materials[i].path.replace(hip, "$HIP")
            else:
                path = materials[i].path
            mtlxnode.parm('file').set(path)

            for a, b in type_dic.items():
                if materials[i].maptype.lower() in b and a == 'height':
                    disp = hou.node(parent.path()).createNode('mtlxdisplacement',
                                                              asset + '_' + materials[i].maptype + '_displacement')
                    disp.setMaterialFlag(False)
                    collect = hou.node(parent.path()).createNode('collect', asset + '_' + materials[i].maptype + '_collect')
                    std.setMaterialFlag(False)
                    disp.setNamedInput('displacement', mtlxnode, 'out')
                    collect.setInput(0, std, 0)
                    collect.setInput(1, disp, 0)

                elif materials[i].maptype.lower() in b and a == 'normal':
                    normap = hou.node(parent.path()).createNode('mtlxnormalmap', asset + '_' + materials[i].maptype + '_normalmap')
                    normap.setNamedInput('in', mtlxnode, 'out')
                    std.setNamedInput('normal', normap, 'out')

                elif materials[i].maptype.lower() in b:
                    std.setNamedInput(a, mtlxnode, 'out')

    try:
        hou.node(parent.path()).layoutChildren()
    except:
        pass


dlg = App()
dlg.show()

# node.setNamedInput('name of input',output node, 'name of output')
# node.setInput(input idx, output node, output idx)  #idx can be retrieved from node type properties menu
# node.layoutChildren()import os
