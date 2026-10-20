import socket


class CongestionControl:
    def __init__(self, MSS: int):
        self.current_state = "slow start"
        self.MSS = MSS
        self.cwnd = MSS
        self.ssthresh = None
        self.repeat = 0

    def get_cwnd(self) -> bytes:
        return int(self.cwnd)

    def get_MSS_in_cwnd(self) -> int:
        return self.cwnd//self.MSS
    
    def event_ack_received(self):
        if self.is_state_slow_start():
            self.cwnd += self.MSS
            if self.get_ssthresh() != None:
                if self.cwnd >= self.get_ssthresh():
                    self.current_state = "congestion avoidance"
        
        else:
            self.cwnd += self.MSS/self.get_MSS_in_cwnd()

    def event_timeout(self):
        if self.is_state_slow_start():
            if self.ssthresh == None:
                self.ssthresh = self.cwnd//2
                self.cwnd = self.MSS
        else:
            self.current_state = "slow start"
            self.ssthresh = self.cwnd//2
            self.cwnd = self.MSS

    def is_state_slow_start(self):
        return self.current_state == "slow start"
    
    def is_state_congestion_avoidance(self):
        return self.current_state == "congestion avoidance"
    
    def get_ssthresh(self):
        return self.ssthresh