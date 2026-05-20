import { mount } from "@vue/test-utils";
import { createMemoryHistory, createRouter } from "vue-router";
import ElementPlus from "element-plus";
import { createPinia, setActivePinia } from "pinia";

import HomeView from "../HomeView.vue";

const router = createRouter({
  history: createMemoryHistory(),
  routes: [{ path: "/", component: HomeView }],
});

describe("HomeView", () => {
  it("renders the main inspection call to action", async () => {
    setActivePinia(createPinia());
    await router.push("/");
    await router.isReady();

    const wrapper = mount(HomeView, {
      global: {
        plugins: [ElementPlus, router],
      },
    });

    expect(wrapper.text()).toContain("输入公开视频链接");
    expect(wrapper.text()).toContain("仅支持公开链接");
  });
});
