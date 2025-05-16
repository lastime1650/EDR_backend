from datetime import datetime, timedelta
import pytz

# 현재 시간-current_time 구하기
def Get_Current_Time()->str:
    utc_time = datetime.now(pytz.timezone('Asia/Seoul'))
    iso_format_with_z = utc_time.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
    return iso_format_with_z

# current_time 기준 이후 시간 만들기
def Set_Increase_Time(current_time: str, Days: int = None, Hours: int = None, Minutes: int = None,
                      Seconds: int = None) -> str:
    utc_time = datetime.strptime(current_time, '%Y-%m-%dT%H:%M:%S.%fZ')

    if Days:
        utc_time += timedelta(days=Days)
    if Hours:
        utc_time += timedelta(hours=Hours)
    if Minutes:
        utc_time += timedelta(minutes=Minutes)
    if Seconds:
        utc_time += timedelta(seconds=Seconds)

    iso_format_with_z = utc_time.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
    return iso_format_with_z

# current_time 기준 이전 시간 만들기
def Set_Decrease_Time(current_time: str, Days: int = None, Hours: int = None, Minutes: int = None,
                      Seconds: int = None) -> str:
    utc_time = datetime.strptime(current_time, '%Y-%m-%dT%H:%M:%S.%fZ')

    if Days:
        utc_time -= timedelta(days=Days)
    if Hours:
        utc_time -= timedelta(hours=Hours)
    if Minutes:
        utc_time -= timedelta(minutes=Minutes)
    if Seconds:
        utc_time -= timedelta(seconds=Seconds)

    iso_format_with_z = utc_time.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
    return iso_format_with_z

def Set_Range_Time(current_time: str=None, Days: int = None, Hours: int = None, Minutes: int = None,
                      Seconds: int = None) -> (str,str,str):

    if not current_time:
        current_time = Get_Current_Time()
    print(current_time)

    output_current_time = current_time
    output_increased_time = ""
    output_decreased_time = ""

    if Days:

        output_increased_time = Set_Increase_Time(current_time, Days=Days)

        output_decreased_time = Set_Decrease_Time(current_time, Days=Days)

    if Hours:
        output_increased_time = Set_Increase_Time(current_time, Hours=Hours)

        output_decreased_time = Set_Decrease_Time(current_time, Hours=Hours)

    if Minutes:
        output_increased_time = Set_Increase_Time(current_time, Minutes=Minutes)

        output_decreased_time = Set_Decrease_Time(current_time, Minutes=Minutes)

    if Seconds:
        output_increased_time = Set_Increase_Time(current_time, Seconds=Seconds)

        output_decreased_time = Set_Decrease_Time(current_time, Seconds=Seconds)


    return output_current_time, output_increased_time, output_decreased_time



'''current = Get_Current_Time()
print(current)

print(Set_Increase_Time(current, Days=1))

print(Set_Decrease_Time(current, Days=1))

print(Set_Range_Time(Days=1))
'''