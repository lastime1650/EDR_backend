import json

from langchain.memory import ConversationBufferMemory
import pickle
import os
from typing import Any, Optional, List, Dict, Tuple
# 대화 메모리 공유 클래스
class Share_ConversationMemory():
    def __init__(self):
        self.share_memory = {} # EDR core-server간 분석 전용



        return

    # 대화 메모리 추가하기
    def Add_Conversation(self, ConversationID:str)->Optional[ConversationBufferMemory]:
        if ConversationID in self.share_memory:
            # 현 메인 메모리에 없는 경우, HDD에서 가져올 수 있는 지 체크
            return self.Get_Conversation(
                ConversationID=ConversationID,
                is_from_hdd=True
            )
        else:
            # 새로 추가
            self.share_memory[ConversationID] = ConversationBufferMemory(memory_key=ConversationID, return_messages=True)
            
            # 방금 추가한 대화 메모리 저장하기
            #self.Save_Conversation(ConversationID)

            return self.share_memory[ConversationID]

    # 대화 메모리 가져오기
    def Get_Conversation(self, ConversationID:str, is_from_hdd:bool=False, need_save_mainmemory:bool=False)->Optional[ConversationBufferMemory]:
        if ConversationID in self.share_memory:
            return self.share_memory[ConversationID]
        else:
            if is_from_hdd:
                try:
                    ConversationBuffer:Optional[ConversationBufferMemory] = None
                    with open(fr"C:\Users\Administrator\Desktop\My_Python_Prj\NewGen_EDR\pythonProject\_LLM_Server_\{ConversationID}.memory", "rb") as f:
                        ConversationBuffer = pickle.load(f)

                    if need_save_mainmemory:
                        self.share_memory[ConversationID] = ConversationBuffer

                    return ConversationBuffer

                except:
                    return None

            else:
                return None


    # 대화 메모리 HDD 저장
    def Save_Conversation_from_buff(self, ConversationID:str,ConversationBuff:ConversationBufferMemory):
        with open(f"{ConversationID}.memory", "wb") as f:
            pickle.dump(ConversationBuff, f)

    #def Save_Conversation(self, ConversationID:str,is_update:bool=False)->bool:

    # 대화 메모리 삭제
    def Delete_Conversation(self, ConversationID:str, is_hdd_mode:bool=False)->bool:
        if ConversationID in self.share_memory:
            del self.share_memory[ConversationID]
            return True
        else:
            if is_hdd_mode:
                os.remove(f"{ConversationID}.memory")
                return True
            else:
                return False
            return False

    # 대화 카피
    def _copy_src_to_dst(self, src:ConversationBufferMemory, dst:ConversationBufferMemory):

        # 모두 카피
        it = iter(src.chat_memory.messages)
        for message in it:
            dst.chat_memory.add_user_message(message.content)
            dst.chat_memory.add_ai_message(next(it).content)

    # 대화 이력 -> list
    def output_Conversation_history(self, ConversationBuff:ConversationBufferMemory)->List[Dict]:
        output_messages:List[Dict] = []

        # 모두 카피
        it = iter(ConversationBuff.chat_memory.messages)
        for message in it:

            user_message = message.content
            try:
                dict_message = json.loads(user_message)
                for key in dict_message:
                    if "input" in key:
                        user_message = dict_message[key]
                        break
            except:
                pass

            output_messages.append( {
                "user": user_message,
                "ai": next(it).content
            })

        return output_messages

class Agent_Chatbot_Memory(Share_ConversationMemory):
    def __init__(self):
        super().__init__()
    def Create_ChatSession(self, Conversation_ID:str)->Optional[ConversationBufferMemory]:
        if Conversation_ID in self.share_memory:
            return None
        else:
            self.share_memory[Conversation_ID] = ConversationBufferMemory(memory_key=Conversation_ID, return_messages=True)
            return self.share_memory[Conversation_ID]

    def Remove_Conversation(self, Conversation_ID:str):
        if Conversation_ID in self.share_memory:
            del self.share_memory[Conversation_ID]
            return True
        else:
            return False

# 대화 메모리 클래스 사용 예시
'''abc = Share_ConversationMemory()
conversation_memory_inst = ConversationBufferMemory(
                memory_key="test",
                return_messages=True
            )
abc.Add_Conversation("test",conversation_memory_inst)
print(abc.share_memory)
abc.Save_Conversation("test")
abc.Delete_Conversation("test", is_hdd_mode=False)
print(abc.share_memory)
abc.Get_Conversation("test", is_from_hdd=True)
print(abc.share_memory)'''
