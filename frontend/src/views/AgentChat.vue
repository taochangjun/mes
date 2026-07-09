<template>
  <div class="agent-chat">
    <h1 class="page-title">AI 助手</h1>
    <p class="subtitle">测试 <code>POST /api/agent/chat</code>（Tool Calling + RAG）</p>

    <div class="chat-layout">
      <div ref="messageListRef" class="message-list">
        <div v-if="messages.length === 0" class="empty-hint">
          <p>输入问题，或点击下方示例快速体验。</p>
        </div>

        <div
          v-for="(msg, index) in messages"
          :key="index"
          class="message-row"
          :class="msg.role"
        >
          <div class="bubble">
            <div class="bubble-role">{{ msg.role === 'user' ? '你' : '助手' }}</div>
            <div class="bubble-content">{{ msg.content }}</div>
            <div v-if="msg.toolCalls?.length" class="tool-calls">
              <div class="tool-label">调用的工具</div>
              <div v-for="(tc, i) in msg.toolCalls" :key="i" class="tool-item">
                <el-tag size="small" type="info">{{ tc.tool }}</el-tag>
                <span class="tool-args">{{ formatArgs(tc.args) }}</span>
              </div>
            </div>
            <div v-if="msg.elapsedMs" class="meta">{{ (msg.elapsedMs / 1000).toFixed(1) }}s</div>
          </div>
        </div>

        <div v-if="loading" class="message-row assistant">
          <div class="bubble loading-bubble">
            <el-icon class="is-loading"><Loading /></el-icon>
            <span>思考中…</span>
          </div>
        </div>
      </div>

      <div class="input-area">
        <div class="examples">
          <span class="examples-label">示例：</span>
          <el-button
            v-for="q in examples"
            :key="q"
            size="small"
            round
            :disabled="loading"
            @click="sendQuestion(q)"
          >
            {{ q }}
          </el-button>
        </div>
        <div class="input-row">
          <el-input
            v-model="input"
            type="textarea"
            :rows="2"
            placeholder="例如：WO-20250706-001 进度怎么样？"
            :disabled="loading"
            @keydown.enter.exact.prevent="handleSend"
          />
          <el-button type="primary" :loading="loading" @click="handleSend">发送</el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { nextTick, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { agentChat } from '../api'

const examples = [
  'WO-20250706-001 进度怎么样？',
  '现在有哪些工单在生产？',
  '液压系统工位要注意什么安全事项？',
  '底盘预装工位有哪些操作步骤？',
]

const input = ref('')
const loading = ref(false)
const messages = ref([])
const messageListRef = ref(null)

function formatArgs(args) {
  if (!args || Object.keys(args).length === 0) return '（无参数）'
  return JSON.stringify(args)
}

async function scrollToBottom() {
  await nextTick()
  const el = messageListRef.value
  if (el) el.scrollTop = el.scrollHeight
}

async function sendQuestion(question) {
  const text = question.trim()
  if (!text || loading.value) return

  messages.value.push({ role: 'user', content: text })
  input.value = ''
  loading.value = true
  await scrollToBottom()

  const started = performance.now()
  try {
    const data = await agentChat(text)
    messages.value.push({
      role: 'assistant',
      content: data.answer || '（无回答）',
      toolCalls: data.tool_calls || [],
      elapsedMs: performance.now() - started,
    })
  } catch (err) {
    const detail = err.response?.data?.detail
    const msg = typeof detail === 'string' ? detail : err.message || '请求失败'
    ElMessage.error(msg)
    messages.value.push({
      role: 'assistant',
      content: `请求失败：${msg}`,
      elapsedMs: performance.now() - started,
    })
  } finally {
    loading.value = false
    await scrollToBottom()
  }
}

function handleSend() {
  sendQuestion(input.value)
}
</script>

<style scoped>
.agent-chat {
  max-width: 900px;
  margin: 0 auto;
}

.subtitle {
  color: var(--text-muted);
  font-size: 14px;
  margin: -12px 0 20px;
}

.subtitle code {
  background: var(--bg-card);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 13px;
}

.chat-layout {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 180px);
  min-height: 420px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 8px;
  overflow: hidden;
}

.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.empty-hint {
  color: var(--text-muted);
  text-align: center;
  padding: 48px 16px;
  font-size: 14px;
}

.message-row {
  display: flex;
  margin-bottom: 16px;
}

.message-row.user {
  justify-content: flex-end;
}

.message-row.assistant {
  justify-content: flex-start;
}

.bubble {
  max-width: 85%;
  padding: 12px 16px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.6;
}

.user .bubble {
  background: #1e3a5f;
  border: 1px solid #2a4a6f;
}

.assistant .bubble {
  background: #141b26;
  border: 1px solid var(--border);
}

.bubble-role {
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: 6px;
}

.bubble-content {
  white-space: pre-wrap;
  word-break: break-word;
}

.tool-calls {
  margin-top: 12px;
  padding-top: 10px;
  border-top: 1px dashed var(--border);
}

.tool-label {
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: 6px;
}

.tool-item {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
  flex-wrap: wrap;
}

.tool-args {
  font-size: 12px;
  color: #94a3b8;
  font-family: ui-monospace, monospace;
}

.meta {
  margin-top: 8px;
  font-size: 11px;
  color: var(--text-muted);
  text-align: right;
}

.loading-bubble {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--text-muted);
}

.input-area {
  border-top: 1px solid var(--border);
  padding: 16px;
  background: #141b26;
}

.examples {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.examples-label {
  font-size: 12px;
  color: var(--text-muted);
}

.input-row {
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.input-row .el-textarea {
  flex: 1;
}

.input-row .el-button {
  flex-shrink: 0;
  height: 52px;
}
</style>
