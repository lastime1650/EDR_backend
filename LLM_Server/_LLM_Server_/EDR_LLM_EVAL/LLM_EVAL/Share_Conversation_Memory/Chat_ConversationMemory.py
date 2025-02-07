# 분석 전용 대화 메모리 공유 클래스
from typing import Optional

from langchain.memory import ConversationBufferMemory

from _LLM_Server_.EDR_LLM_EVAL.LLM_EVAL.Share_Conversation_Memory.Share_converstaion_mem import Share_ConversationMemory

class Chat_Memory_ConversationManager():
    def __init__(self, share_memory_inst:Share_ConversationMemory):
        self.Share_Conversation_Manager = share_memory_inst

        '''
       {
           "question_id1":{
               "ConversationID": ConversationBufferMemory 객체
           }
       }
       '''
        self.Chat_Memory = {}

    def Get_Chat_Memory(self, question_id:str, Conversation_ID:str)->Optional[ConversationBufferMemory]:
        if question_id in self.Chat_Memory:
            if Conversation_ID in self.Chat_Memory[question_id]:
                return self.Chat_Memory[question_id][Conversation_ID]
            else:
                pass
        else:
            self.Chat_Memory[question_id] = {}

        # 이 경우 프로세스 인스턴스 대화 메모리와 상호작용한 적이 없으므로, Load하고 채팅을 위한 메모리를 생성한다.
        Chat_ConversationBufferMemory = ConversationBufferMemory(memory_key=question_id, return_messages=True)
        get_conversation_buff = self.Share_Conversation_Manager.Get_Conversation(Conversation_ID,True)

        # 기존의 것에서 카피
        self.Share_Conversation_Manager._copy_src_to_dst(get_conversation_buff, Chat_ConversationBufferMemory)

        # dict에 저장
        self.Chat_Memory[question_id][Conversation_ID] =Chat_ConversationBufferMemory

        print(self.Chat_Memory[question_id][Conversation_ID])
        return self.Chat_Memory[question_id][Conversation_ID]


    def Delete_Chat_Memory(self, question_id:str, Conversation_ID:str):
        if question_id in self.Chat_Memory:
            if Conversation_ID in self.Chat_Memory[question_id]:
                self.Chat_Memory[question_id].pop(Conversation_ID)