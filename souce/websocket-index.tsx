import { requestData } from "../../../utils/request.ts";
import encrypt from "./encrypt";
import { deepMerge, getCookie } from "../../../utils/index";
import getJdEid from "../../../utils/jdEid";
import { getMaskMsg } from "./msgMask";
import { TopMsgType, MsgBody, IFullMsg } from "./interface";
import mockMsg from "./mock";
interface IMsgWsParams {
  pin?: string;
  secretPin?: string;
  liveId?: string;
  liveTitle?: string; // 直播间标题 （主播端用）
  nickName?: string; // 用户昵称 （C端用）
  plus?: number,
  loveLevel?: number,
  userMemberLevel?: string,
  shopMember?: string,
}
interface IOptions {
  maxReconnectAttempts: number; // 重试次数
  heartbeatTimeout: number; // 超过这个时间没有收到消息就重连(秒)
}

interface IConfig {
  aid?: "dongdong";
  appId?: "jd.mall";
  fromApp?: "jd.live";
  secretKey?: string;
  iv?: string;
  clientType?: "anchor" | "m";
  ver?: string;
}

type ListenerType = "onSuccess" | "onMessage" | "onError" | "onReconnect";

class MsgWebSocket {
  private socket: WebSocket | null = null;
  private params: IMsgWsParams = {};
  private config: IConfig = {
    aid: "dongdong",
    appId: "jd.mall",
    fromApp: "jd.live",
    secretKey: "RYm2dMPMWD9AxYFk",
    iv: "0102030405060708",
    clientType: "anchor",
    ver: "1.0",
  };
  private options: IOptions = {
    maxReconnectAttempts: 5,
    heartbeatTimeout: 30,
  };
  private msgMaskKey: string | null = null;
  private heartbeatTimer: number | null = null;
  private reconnectAttempts: number = 0;
  private isForcedClosure: boolean = false;
  private listeners: { [key in ListenerType]: ((data?: IFullMsg) => void)[] } =
    {
      onSuccess: [], // 建连成功
      onMessage: [], // 收到消息
      onError: [], // 错误
      onReconnect: [], // 重连中
    };

  constructor(clientType: "anchor" | "m", options?: IOptions) {
    this.options = {
      ...this.options,
      ...options,
    };
    this.config = {
      ...this.config,
      clientType,
    };
    this.socket = null;
    // mock
    if (process.env.NODE_ENV === 'development') {
      mockMsg((msg: IFullMsg) => {
        this.handleListers("onMessage", msg);
      });
    }
  }

  public async connect(params: IMsgWsParams) {
    try {
      this.params = params;
      const url = await this.authToGetUrl(params);
      // 频繁切换直播间，没办法撤销鉴权接口请求
      // 判断连接被人为关闭之后就不建立 sock
      if(!this.isForcedClosure) {
        this.socket = new WebSocket(url);
        this.socket.onopen = this.onOpen.bind(this);
        this.socket.onmessage = this.onMessage.bind(this);
        this.socket.onerror = this.onError.bind(this);
        this.socket.onclose = this.onClose.bind(this);
        this.listenToHeartbeat();
      }
    } catch (error) {
      console.error("ws", error);
    }
  }

  private async authToGetUrl(params: IMsgWsParams) {
    const riskJd: { eid?: string } = await getJdEid();
    const content = {
      appId: this.config.appId,
      secretKey: this.config.secretKey,
      clientType: this.config.clientType,
      pin: params.pin,
      eid: riskJd?.eid,
      groupId: params.liveId,
      encryptPin: true, // 是否加密pin
      timestamp: +new Date(),
      random: Math.random().toString(36).slice(-6),
    };
    const res = await requestData("liveauth", {
      content: encrypt(content, this.config.secretKey, this.config.iv),
      appId: this.config.appId,
    });
    if (res) {
      const { liveUrl, token, msgMaskKey, msgMask, secretPin } = res?.data || {};
      if(this.params) {
        this.params.secretPin = secretPin
      }
      this.msgMaskKey = msgMask ? msgMaskKey : null;
      return `${liveUrl}?token=${token}`;
    }
    throw new Error("ws 鉴权失败");
  }

  private async listenToHeartbeat() {
    if (this.heartbeatTimer) {
      clearTimeout(this.heartbeatTimer);
    }
    if (this.reconnectAttempts < this.options.maxReconnectAttempts) {
      this.heartbeatTimer = window.setTimeout(() => {
        this.reconnectAttempts += 1;
        window.clearTimeout(this.heartbeatTimer as number);
        this.reConnectSocket();
        // 标记开始重连
        if (this.reconnectAttempts === 1) {
          this.handleListers("onReconnect");
        }
      }, this.options.heartbeatTimeout * 1000);
    } else {
      this.handleListers("onError");
    }
  }
  private reConnectSocket() {
    this.closeConnection();
    this.connect(this.params);
  }

  private async handleMessage(event: MessageEvent) {
    try {
      const msg = JSON.parse(await getMaskMsg(this.msgMaskKey, event.data));
      if (!msg) {
        this.closeConnection();
        return;
      }
      this.handleListers("onMessage", msg);
      // 收到 onOpen 后发送 create_chat_group 的回执
      // code 2xx表示链接创建成功
      if (
        msg.type === TopMsgType.RESULT &&
        /^2\d{2}$/.test((msg.body?.code).toString())
      ) {
        this.handleListers("onSuccess", msg);
      }
    } catch (error) {
      this.closeConnection();
    }
  }

  private onOpen(event: Event) {
    if (this.config.clientType === "anchor") {
      this.sendCreateChatGroupMsg();
    } else {
      this.sendJoinMsg();
    }
    console.log("WebSocket connection opened:", event);
  }

  private onMessage(event: MessageEvent) {
    this.handleMessage(event);
    this.isForcedClosure = false;
    this.reconnectAttempts = 0;
    this.listenToHeartbeat();
    // console.log('WebSocket message received:', event.data);
  }

  private onError(event: Event) {
    if (!this.isForcedClosure) {
      this.reConnectSocket();
    }
    console.error("WebSocket error:", event);
  }

  // eslint-disable-next-line class-methods-use-this
  private onClose(event: CloseEvent) {
    console.log("WebSocket connection closed:", event);
  }

  private async sendCreateChatGroupMsg() {
    if (this.socket?.send) {
      this.socket.send(
        await this.getFullUpMsg("create_chat_group", {
          name: this.params.liveTitle,
          intro: "2",
          owner: this.params.pin,
          kind: "live_broadcast",
          liveKind: "live_broadcast",
        })
      );
    }
  }

  private async sendJoinMsg() {
    if (this.socket?.send) {
      this.socket.send(
        await this.getFullUpMsg("chat_group_message", {
          type: "join_live_broadcast",
          nickName: this.params.nickName,
          groupid: this.params.liveId,
        })
      );
    }
  }

  private handleListers(type: ListenerType, data?: any) {
    const callbacks = this.listeners?.[type];
    if (Array.isArray(callbacks) && callbacks.length) {
      callbacks.forEach((handler) => handler(data));
    }
  }

  public async getFullUpMsg(type: string, body: any): Promise<string> {
    const riskJd: { eid?: string } = await getJdEid();
    const { nickName, plus, loveLevel, liveId, userMemberLevel, shopMember, secretPin } = this.params || {}
    return JSON.stringify({
      aid: this.config.aid,
      id: new Date().getTime().toString(), // 操控台是uid?
      groupid: this.params.liveId,
      from: {
        app: this.config.fromApp,
        // pin,
        secretPin,
        clientType: this.config.clientType,
        dvc: getCookie("__jda").split(".")[1],
      },
      type,
      ver: "1.0.0",
      body: deepMerge(
        {
          groupid: liveId,
          broadcast: 1,
          number: 1,
          nickName,
          plus,
          loveLevel,
          userMemberLevel,
          shopMember,
          // sort,
          content: body.content,
          type: body.type,
          ext: {
            eid: riskJd?.eid,
            ver: "1.1",
            appid: this.config.appId,
          },
        },
        body
      ),
    });
  }
  public async sendMessage(body: MsgBody) {
    if (this.isForcedClosure) {
      this.reConnectSocket();
      return;
    }
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.send(await this.getFullUpMsg("chat_group_message", body));
    } else if (this.socket?.readyState === WebSocket.CONNECTING) {
      setTimeout(() => {
        this.sendMessage(body);
      }, 500);
    } else {
      this.reConnectSocket();
    }
  }

  // 关闭连接，释放监听等
  public closeConnection() {
    this.isForcedClosure = true;
    this.removeListenerAll()
    if (this.socket?.close) {
      this.socket.close();
      this.socket = null
    }
    clearTimeout(this.heartbeatTimer);
  }

  public addListener(type: ListenerType, callback: (msg: IFullMsg) => void) {
    if (Array.isArray(this.listeners?.[type])) {
      this.listeners[type].push(callback);
    }
  }
  public removeListener(type: ListenerType) {
    if (Array.isArray(this.listeners?.[type])) {
      this.listeners[type] = [];
    }
  }

  public removeListenerAll() {
    for (const type in this.listeners) {
      if (Array.isArray(this.listeners?.[type as ListenerType])) {
        this.listeners[type as ListenerType] = [];
      }
    }
  }
}

export default MsgWebSocket;
