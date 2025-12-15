# backend/websocket_handler.py
"""
WebSocket处理器
处理Agent主机的WebSocket连接和消息
"""
import json
import asyncio
from typing import Dict, Set
from fastapi import WebSocket, WebSocketDisconnect
from backend.agent_host_manager import AgentHostManager

# 存储活跃的连接
active_connections: Dict[str, WebSocket] = {}


class ConnectionManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        self.manager = AgentHostManager()
    
    async def connect(self, websocket: WebSocket, token: str) -> bool:
        """连接WebSocket并验证token"""
        # 验证token
        host = self.manager.get_agent_host_by_token(token)
        if not host:
            await websocket.close(code=1008, reason="Invalid token")
            return False
        
        host_id = host["host_id"]
        
        # 如果已有连接，先关闭旧连接
        if host_id in active_connections:
            try:
                old_ws = active_connections[host_id]
                await old_ws.close(code=1000, reason="New connection")
            except:
                pass
        
        # 接受连接
        await websocket.accept()
        
        # 保存连接
        active_connections[host_id] = websocket
        
        # 更新主机状态
        self.manager.update_host_status(host_id, "online")
        
        print(f"✅ Agent主机连接成功: {host_id} ({host['name']})")
        return True
    
    def disconnect(self, host_id: str):
        """断开连接"""
        if host_id in active_connections:
            del active_connections[host_id]
            # 更新主机状态
            self.manager.update_host_status(host_id, "offline")
            print(f"✅ Agent主机断开连接: {host_id}")
    
    async def send_message(self, host_id: str, message: dict):
        """向指定主机发送消息"""
        if host_id in active_connections:
            websocket = active_connections[host_id]
            try:
                await websocket.send_json(message)
                return True
            except Exception as e:
                print(f"⚠️ 发送消息失败: {e}")
                self.disconnect(host_id)
                return False
        return False
    
    async def broadcast(self, message: dict):
        """向所有连接的主机广播消息"""
        disconnected = []
        for host_id, websocket in active_connections.items():
            try:
                await websocket.send_json(message)
            except Exception as e:
                print(f"⚠️ 广播消息失败 ({host_id}): {e}")
                disconnected.append(host_id)
        
        # 清理断开的连接
        for host_id in disconnected:
            self.disconnect(host_id)
    
    def get_connected_hosts(self) -> Set[str]:
        """获取所有已连接的主机ID"""
        return set(active_connections.keys())


# 全局连接管理器实例
connection_manager = ConnectionManager()


async def handle_agent_websocket(websocket: WebSocket, token: str):
    """处理Agent WebSocket连接"""
    manager = AgentHostManager()
    
    # 验证token并连接
    host = manager.get_agent_host_by_token(token)
    if not host:
        await websocket.close(code=1008, reason="Invalid token")
        return
    
    host_id = host["host_id"]
    
    # 连接
    if not await connection_manager.connect(websocket, token):
        return
    
    try:
        # 发送欢迎消息
        await websocket.send_json({
            "type": "welcome",
            "message": "连接成功",
            "host_id": host_id
        })
        
        # 处理消息
        while True:
            try:
                # 接收消息
                data = await websocket.receive_text()
                
                try:
                    message = json.loads(data)
                except json.JSONDecodeError:
                    await websocket.send_json({
                        "type": "error",
                        "message": "无效的JSON格式"
                    })
                    continue
                
                message_type = message.get("type")
                
                if message_type == "heartbeat":
                    # 心跳消息
                    host_info = message.get("host_info", {})
                    docker_info = message.get("docker_info", {})
                    
                    # 更新主机状态和信息
                    manager.update_host_status(
                        host_id,
                        "online",
                        host_info=host_info,
                        docker_info=docker_info
                    )
                    
                    # 回复心跳
                    await websocket.send_json({
                        "type": "heartbeat_ack",
                        "timestamp": message.get("timestamp")
                    })
                
                elif message_type == "host_info":
                    # 主机信息上报
                    host_info = message.get("host_info", {})
                    docker_info = message.get("docker_info", {})
                    
                    manager.update_host_status(
                        host_id,
                        "online",
                        host_info=host_info,
                        docker_info=docker_info
                    )
                    
                    await websocket.send_json({
                        "type": "host_info_ack",
                        "message": "主机信息已更新"
                    })
                
                elif message_type == "command_result":
                    # 命令执行结果
                    command_id = message.get("command_id")
                    result = message.get("result")
                    # 这里可以处理命令执行结果
                    print(f"📥 收到命令执行结果 ({host_id}): {command_id}")
                
                elif message_type == "deploy_result":
                    # 部署任务执行结果
                    task_id = message.get("task_id")
                    deploy_status = message.get("status")
                    deploy_message = message.get("message")
                    deploy_result = message.get("result")
                    
                    print(f"📥 收到部署任务结果 ({host_id}): {task_id}, 状态: {deploy_status}")
                    
                    # 更新部署任务状态（使用BuildTaskManager）
                    try:
                        from backend.handlers import BuildTaskManager
                        build_manager = BuildTaskManager()
                        
                        # 获取任务信息以找到目标名称
                        task = build_manager.get_task(task_id)
                        if task and task.get("task_type") == "deploy":
                            # 查找对应的目标（通过 host_id）
                            task_config = task.get("task_config", {})
                            config = task_config.get("config", {})
                            targets = config.get("targets", [])
                            target_name = None
                            for target in targets:
                                if target.get("mode") == "agent":
                                    agent_name = target.get("agent", {}).get("name")
                                    if agent_name == host.get("name"):
                                        target_name = target.get("name")
                                        break
                            
                            # 添加日志
                            if deploy_status == "completed":
                                build_manager.add_log(task_id, f"✅ 目标 {target_name} 部署成功: {deploy_message}\n")
                            elif deploy_status == "failed":
                                error_msg = message.get("error", deploy_message)
                                build_manager.add_log(task_id, f"❌ 目标 {target_name} 部署失败: {error_msg}\n")
                            
                            # 更新任务状态
                            if deploy_status == "completed":
                                # 检查是否所有目标都已完成
                                # 这里简化处理，如果收到成功消息，任务可能已完成
                                build_manager.update_task_status(task_id, "completed")
                            elif deploy_status == "failed":
                                build_manager.update_task_status(task_id, "failed", error=deploy_message)
                    except Exception as e:
                        print(f"⚠️ 更新部署任务状态失败: {e}")
                        import traceback
                        traceback.print_exc()
                    
                    # 回复确认
                    await websocket.send_json({
                        "type": "deploy_result_ack",
                        "task_id": task_id,
                        "message": "部署结果已接收"
                    })
                
                else:
                    # 未知消息类型
                    await websocket.send_json({
                        "type": "error",
                        "message": f"未知的消息类型: {message_type}"
                    })
            
            except WebSocketDisconnect:
                break
            except Exception as e:
                print(f"⚠️ 处理消息时出错 ({host_id}): {e}")
                try:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"处理消息失败: {str(e)}"
                    })
                except:
                    break
    
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"⚠️ WebSocket连接错误 ({host_id}): {e}")
    finally:
        # 断开连接
        connection_manager.disconnect(host_id)

