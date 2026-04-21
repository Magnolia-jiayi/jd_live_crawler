import request from "../utils/request";
import getJdEid from "../utils/jdEid";

export function liveDetailToM(params) {
  return request({
    url: "liveDetailToM",
    method: "get",
    params: {
      functionId: "liveDetailToM",
      appid: "h5-live",
      body: params,
      t: new Date().getTime(),
    },
  });
}
export function recommendationListToM(params, commonParams = {}) {
  return request({
    url: "/api",
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded;charset=utf-8",
    },
    data: {
      functionId: "recommendationListToM",
      appid: "live_pc",
      ...commonParams,
      body: JSON.stringify({
        ...params,
      }),
      t: new Date().getTime(),
    },
  });
}

// 精选 | 推荐 列表
// 文档：https://joyspace.jd.com/pages/9xPLs3DjIpzXiXWYUhar
export function predictLiveListToM(params, commonParams = {}) {
  return request({
    url: "/api",
    method: "POST",
    params: {
      functionId: "predictLiveListToM",
      appid: "live_pc",
      ...commonParams,
      body: JSON.stringify({
        ...params,
      }),
      t: new Date().getTime(),
    },
  });
}

// 直播间上下滑动
// 文档：https://joyspace.jd.com/pages/MjAhTUQzDNfK4gvOnLVt
export function pageDownListToM(params, commonParams = {}) {
  return request({
    url: "/api",
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded;charset=utf-8",
    },
    data: {
      functionId: "pageDownListToM",
      appid: "live_pc",
      ...commonParams,
      body: JSON.stringify({
        ...params,
      }),
      t: new Date().getTime(),
    },
  });
}

// 直播间详情
// 文档：https://joyspace.jd.com/pages/2QaGTtiEgfXfGnOdKnKD
export function liveBasicDetailToM(params, commonParams = {}) {
  return request({
    url: "/api",
    method: "GET",
    params: {
      functionId: "liveBasicDetailToM",
      appid: "live_pc",
      ...commonParams,
      body: JSON.stringify({
        ...params,
      }),
      t: new Date().getTime(),
    },
  });
}

// 拉流接口
// https://joyspace.jd.com/pages/L8KJDeztSiJwsMTKLTtt
export function getImmediatePlayToM(params, commonParams = {}) {
  return request({
    url: "/api",
    method: "GET",
    params: {
      functionId: "getImmediatePlayToM",
      appid: "live_pc",
      ...commonParams,
      body: JSON.stringify({
        ...params,
      }),
      t: new Date().getTime(),
    },
  });
}

export async function msgFilterToM(body) {
  const riskJd = await getJdEid();
  return request({
    url: "/api",
    method: "GET",
    params: {
      functionId: "msgFilterToM",
      appid: "live_pc",
      v: new Date().getTime(),
      body: JSON.stringify({
        ...body,
        eid: riskJd.eid,
        type: "viewer_send_message",
      }),
    },
  });
}
