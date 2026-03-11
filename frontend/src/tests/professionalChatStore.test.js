import { describe, it, expect, beforeEach, vi } from "vitest"
import { setActivePinia, createPinia } from "pinia"
import { useProfessionalChatStore } from "@/stores/professionalChatStore"
import * as service from "@/services/professionalChatService"
import { useAuthStore } from "@/stores/authStore"

// Mock services and authStore
vi.mock("@/services/professionalChatService")
vi.mock("@/stores/authStore")

describe("ProfessionalChatStore", () => {
  let store
  let authStoreMock

  beforeEach(() => {
    setActivePinia(createPinia())
    store = useProfessionalChatStore()

    // Mock authStore
    authStoreMock = {
      getCurrentUserID: "prof-123",
    }
    useAuthStore.mockReturnValue(authStoreMock)

    // Reset state
    store.queues.waiting = []
    store.queues.in_progress = []
    store.queues.closed = []
    store.activeChat = null
    store.loading = {
      queues: false,
      chat: false,
      claim: false,
      close: false,
      send: false,
    }
  })

  it("initializeQueues should populate queues", async () => {
    service.fetchQueues.mockResolvedValue({
      waiting: [{ id: "w1" }],
      in_progress: [{ id: "i1" }],
      closed: [{ id: "c1" }],
    })

    await store.initializeQueues()

    expect(store.queues.waiting).toHaveLength(1)
    expect(store.queues.in_progress).toHaveLength(1)
    expect(store.queues.closed).toHaveLength(1)
    expect(store.loading.queues).toBe(false)
  })

  it("openChat should fetch and set activeChat", async () => {
    const chatData = { id: "chat1", messages: [] }
    service.fetchChat.mockResolvedValue(chatData)

    await store.openChat("chat1")

    expect(store.activeChat).toEqual(chatData)
    expect(store.loading.chat).toBe(false)
  })

  it("claimChat should move chat from waiting to in_progress", async () => {
    store.queues.waiting.push({
      id: "w1",
      status: "waiting_for_professional",
      assigned_professional_id: null,
    })
    store.activeChat = {
      id: "w1",
      status: "waiting_for_professional",
      assigned_professional_id: null,
    }

    service.claim.mockResolvedValue({})

    await store.claimChat("w1")

    expect(store.queues.waiting).toHaveLength(0)
    expect(store.queues.in_progress).toHaveLength(1)
    expect(store.queues.in_progress[0].status).toBe("in_progress")
    expect(store.activeChat.status).toBe("in_progress")
  })

  it("unclaimChat should move chat from in_progress to waiting", async () => {
    store.queues.in_progress.push({
      id: "i1",
      status: "in_progress",
      assigned_professional_id: "prof-123",
    })
    store.activeChat = {
      id: "i1",
      status: "in_progress",
      assigned_professional_id: "prof-123",
    }

    service.unclaim.mockResolvedValue({})

    await store.unclaimChat("i1")

    expect(store.queues.in_progress).toHaveLength(0)
    expect(store.queues.waiting).toHaveLength(1)
    expect(store.queues.waiting[0].status).toBe("waiting_for_professional")
    expect(store.activeChat.status).toBe("waiting_for_professional")
  })

  it("closeChat should move chat to closed", async () => {
    store.queues.in_progress.push({
      id: "i1",
      status: "in_progress",
      assigned_professional_id: "prof-123",
    })
    store.activeChat = {
      id: "i1",
      status: "in_progress",
      assigned_professional_id: "prof-123",
    }

    service.close.mockResolvedValue({})

    await store.closeChat("i1")

    expect(store.queues.in_progress).toHaveLength(0)
    expect(store.queues.closed).toHaveLength(1)
    expect(store.queues.closed[0].status).toBe("closed")
    expect(store.activeChat.status).toBe("closed")
  })

  it("sendProfessionalMessage should add message to activeChat", async () => {
    const savedMessage = { id: "m1", content: "Hello" }
    service.addProfessionalMessage.mockResolvedValue(savedMessage)

    store.activeChat = { id: "chat1", messages: [] }

    await store.sendProfessionalMessage("Hello")

    expect(store.activeChat.messages).toHaveLength(1)
    expect(store.activeChat.messages[0]).toEqual(savedMessage)
  })
})
