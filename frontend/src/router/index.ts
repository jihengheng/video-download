import { createRouter, createWebHistory } from "vue-router";

import HistoryView from "../views/HistoryView.vue";
import HomeView from "../views/HomeView.vue";
import InspectView from "../views/InspectView.vue";
import ResultView from "../views/ResultView.vue";
import TaskDetailView from "../views/TaskDetailView.vue";
import WorkspaceView from "../views/WorkspaceView.vue";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", name: "home", component: HomeView },
    { path: "/inspect", name: "inspect", component: InspectView },
    { path: "/workspace/tasks", name: "workspace", component: WorkspaceView },
    { path: "/workspace/tasks/:id", name: "task-detail", component: TaskDetailView, props: true },
    { path: "/results/:id", name: "result", component: ResultView, props: true },
    { path: "/history", name: "history", component: HistoryView },
  ],
});

export default router;
