# Mermaid Graph 생성 모듈

from typing import Optional, List, Any, Dict, Union, Tuple

from enum import Enum
class Mermaid_Maker__Graph_Flow(Enum):
    LR = 1
    TD = 2
    TB = 3
class Mermaid_Maker__Graph_Shape(Enum):
    rectangle = 1
    circle = 2
    diamond = 3


class Mermaid_Graph_Maker():
    def __init__(self, Main_Node_Flow:Mermaid_Maker__Graph_Flow=None):


        self.Mermaid_graph_string = "" # 최종형

        if Main_Node_Flow:
            self.Mermaid_graph_string += f"graph {Main_Node_Flow.name}\n"
        else:
            self.Mermaid_graph_string += f"graph TD\n"

        self.Auto_Src_Node_ID = 1 # 자동 생성 노드 ID # 노드 식별
        self.Auto_Dest_Node_ID = 1  # 자동 생성 노드 ID # 노드 식별
        self.Auto_Edge_ID = 1 # 자동 생성 에지 ID # 연결 선

        self.Auto_Sub_Node_ID = 1 # 자동 생성 서브 노드 ID # 서브 노드 식별
        self.Auto_Sub_Edge_ID = 1 # 서브 노드 에지 # 연결 선

        self.monitor_sub_graph = {} # 서브 그래프 모니터링 ( 중복 start 및 end 가능 체크 )

        self.Auto_SubGraph_Style_Color_num = 0 # 자동 생성 서브 그래프 스타일 폰트 색상 번호

        self.linestyle_num:Optional[int] = None

        return
    def Complete_Graph(self)->str:
        return self.Mermaid_graph_string

    def Add_New_Node(
            self,
            src_Node_Label:str, dest_Node_Label:str,
            src_Node_Type: Mermaid_Maker__Graph_Shape = None, dest_Node_Type:Mermaid_Maker__Graph_Shape = None,

            Node_Edge_Label:str=None,

            src_color:str=None,dest_color:str=None,
    )->Tuple[str, str]:

        # -- 시작 노드 ID 설정
        src_node_id = self.Generate_Node_ID_(is_dest_node=False, is_sub_node=False)
        # -- 끝 노드 ID 설정
        dest_node_id = self.Generate_Node_ID_(is_dest_node=True, is_sub_node=False)


        # 노드 추가
        src_node = self.Create_Node_with_Type_(src_node_id,src_Node_Label,src_Node_Type)
        edge = self.Create_Node_Edge_(None)
        dest_node = self.Create_Node_with_Type_(dest_node_id,dest_Node_Label,dest_Node_Type)

        self.append_graph_string_(

            f"{src_node}{edge}{dest_node}"

        )

        # 스타일 추가
        self.append_graph_string_(  self.Create_Style_(src_node_id,src_color)    )
        self.append_graph_string_(  self.Create_Style_(dest_node_id,dest_color)  )

        # 노드 생성 수 모니터링
        if self.linestyle_num == None:
            self.linestyle_num = 0
        else:
            self.linestyle_num += 1


        print(self.Mermaid_graph_string)
        return src_node_id, dest_node_id

    def Connect_Node(
            self,
            dest_Node_Label: str,
            dest_Node_Type: Mermaid_Maker__Graph_Shape = None,
            Node_Edge_Label: str = None,
            dest_color: str = "white",
            line_color: str = "white",
            line_size: int = 24,

            src_node_id_parm:str = None,# 이을 시작 노드 id를 알고 있으면 ~ 연결한다
    )->str:

        dest_node_id = self.Generate_Node_ID_(is_dest_node=True, is_sub_node=False)

        # src 설정
        src_node_id = ''
        if src_node_id_parm:
            src_node_id = src_node_id_parm
        else:
            src_node_id = self.Generate_Node_ID_(is_dest_node=False, is_sub_node=False)

        # 노드 추가
        src_node = src_node_id
        edge = self.Create_Node_Edge_(Node_Edge_Label)
        dest_node = self.Create_Node_with_Type_(dest_node_id, dest_Node_Label, dest_Node_Type)

        self.append_graph_string_(

            f"{src_node}{edge}{dest_node}"

        )

        # dest Style 추가
        self.append_graph_string_(
            self.Create_Style_(dest_node_id, dest_color)
        )

        # 노드 생성 수 모니터링
        if self.linestyle_num == None:
            self.linestyle_num = 0
        else:
            self.linestyle_num += 1


        # lineStyle 추가
        if line_color or line_size:
            self.append_graph_string_(
                self.Create_LineStyle_( line_color, line_size)
            )

        print( self.Mermaid_graph_string)

        return dest_node_id


    def Open_SubGraph(self, sub_graph_name:str, color:str="#000000", protect_mode:bool=False)->bool:
        if protect_mode:
            if sub_graph_name in self.monitor_sub_graph:
                return False
            else:
                self.append_graph_string_(f"subgraph {sub_graph_name}")
                self.monitor_sub_graph[sub_graph_name] = True # linkStyle 0 stroke:red,stroke-width:2px;
                self.append_graph_string_(self.Create_Style_(sub_graph_name, color))
                return True
        else:
            self.append_graph_string_(f"subgraph {sub_graph_name}")
            self.append_graph_string_(self.Create_Style_(sub_graph_name, color))
            return True

    def End_SubGraph(self, sub_graph_name:str, font_color:str="red", protect_mode:bool=False)->bool:
        if protect_mode:
            if sub_graph_name in self.monitor_sub_graph:
                if self.monitor_sub_graph[sub_graph_name]:
                    self.append_graph_string_(f"end")
                    self.monitor_sub_graph[sub_graph_name] = False
                else:
                    return False
        else:
            self.append_graph_string_(f"end")
            self.append_graph_string_(f"classDef C{self.Auto_SubGraph_Style_Color_num} color:{font_color}\n class {sub_graph_name} C{self.Auto_SubGraph_Style_Color_num}")
            self.Auto_SubGraph_Style_Color_num += 1
            return True


    def Connect_SubGraph(self, src_subgraph_name:str, dest_subgraph_name:str):
        self.append_graph_string_(f"{src_subgraph_name} --> {dest_subgraph_name}")
        return


    def append_graph_string_(self, graph_str:str):
        self.Mermaid_graph_string += f"{graph_str}\n"

    ### [유틸] ###

    # Style 생성기
    def Create_Style_(self, node_id:str, color:str)->str:
        selected_src_color = ''
        if color:
            selected_src_color = color
        elif color == '#000000':
            selected_src_color = "white"
        else:
            selected_src_color = "white"

        return f"style {node_id} fill:{selected_src_color}"

    # lineStyle 생성기
    def Create_LineStyle_(self, color: str , line_size: int) -> str:
        selected_src_color = ''
        if color:
            selected_src_color = color
        elif color == '#000000':
            selected_src_color = "white"
        else:
            selected_src_color = "white"

        return f"linkStyle {self.linestyle_num} stroke-width:{line_size}px,stroke:{selected_src_color} "

    # Node하나 만들기
    def Create_Node_with_Type_(self, node_id:str, node_label:str, node_type:Mermaid_Maker__Graph_Shape)->str:

        Node = ''
        if node_type == Mermaid_Maker__Graph_Shape.rectangle:
            Node= f"{node_id}[{node_label}]"
        elif node_type == Mermaid_Maker__Graph_Shape.circle:
            Node= f"{node_id}(({node_label}))"
        else:
            Node= f"{node_id}[{node_label}]"

        return Node

    # 연결선 에지 만들기
    def Create_Node_Edge_(self, Node_Edge_Label:str=None)->str:
        selected_node_edge_label = ""
        if Node_Edge_Label:
            selected_node_edge_label = f" -- {Node_Edge_Label} --> "
        else:
            selected_node_edge_label = " --> "
        return selected_node_edge_label

    # node_id 생성기
    def Generate_Node_ID_(self, is_dest_node:bool, is_sub_node:bool)->str:
        node_id = ''
        if is_sub_node == False:
            if is_dest_node:
                node_id = f"D{self.Auto_Dest_Node_ID}"
                self.Auto_Dest_Node_ID += 1
            else:
                node_id = f"S{self.Auto_Src_Node_ID}"
                self.Auto_Src_Node_ID += 1
        else:
            pass
        return node_id

