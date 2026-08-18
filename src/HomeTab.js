import React from 'react';

export default class HomeTab extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      tasks: []
    };
  }

  componentDidMount() {
    fetch('http://localhost:3001/api/v1/clients')
      .then(res => res.json())
      .then(tasks => {
        tasks.sort((a, b) => a.priority - b.priority);
        this.setState({ tasks });
      })
      .catch(err => console.error("Error fetching tasks for dashboard", err));
  }

  render() {
    const { tasks } = this.state;
    const pendingCount = tasks.filter(t => t.status !== 'complete').length;
    const completedCount = tasks.filter(t => t.status === 'complete').length;
    const upcomingTasks = tasks.filter(t => t.status === 'backlog').slice(0, 3);

    return (
      <div className="bg-background text-on-surface font-body-lg min-h-screen">
        <main className="max-w-7xl mx-auto px-md md:px-lg py-md space-y-lg">
          {/* Welcome Banner Card */}
          <section className="industrial-pattern rounded-xl p-lg relative overflow-hidden shadow-sm">
            <div className="relative z-10 space-y-sm max-w-2xl">
              <h2 className="font-headline-lg-mobile text-headline-lg-mobile text-on-primary">Welcome back to Shiptivitas!</h2>
              <p className="font-body-lg text-on-primary-container opacity-90 leading-relaxed">
                We simplify the task log across your site and help you master the time-sensitive nature of every freight shipping task.
              </p>
            </div>
            {/* Atmospheric Element */}
            <div className="absolute right-0 top-0 h-full w-1/3 opacity-20 pointer-events-none hidden md:block">
              <span className="material-symbols-outlined text-[120px] absolute -right-4 -top-4 text-white" data-icon="conveyor_belt">conveyor_belt</span>
            </div>
          </section>

          {/* Metric Cards */}
          <section className="flex overflow-x-auto no-scrollbar md:grid md:grid-cols-3 gap-md pb-base">
            {/* Metric 1 */}
            <div className="min-w-[260px] flex-1 bg-surface-container-lowest border border-outline-variant rounded-xl p-md flex flex-col justify-between hover:border-primary transition-colors cursor-default group">
              <div className="flex justify-between items-start">
                <span className="font-label-caps text-label-caps text-on-surface-variant uppercase">Tasks Pending</span>
                <span className="material-symbols-outlined text-on-surface-variant group-hover:text-primary transition-colors" data-icon="pending_actions">pending_actions</span>
              </div>
              <div className="mt-lg">
                <span className="font-display-lg text-display-lg text-primary">{pendingCount}</span>
                <div className="flex items-center gap-1 mt-1">
                  <span className="material-symbols-outlined text-error text-sm" data-icon="priority_high">priority_high</span>
                  <span className="font-body-sm text-body-sm text-error">Check board for details</span>
                </div>
              </div>
            </div>
            {/* Metric 2 */}
            <div className="min-w-[260px] flex-1 bg-surface-container-lowest border border-outline-variant rounded-xl p-md flex flex-col justify-between hover:border-primary transition-colors cursor-default group">
              <div className="flex justify-between items-start">
                <span className="font-label-caps text-label-caps text-on-surface-variant uppercase">Tasks Completed</span>
                <span className="material-symbols-outlined text-on-surface-variant group-hover:text-secondary transition-colors" data-icon="task_alt">task_alt</span>
              </div>
              <div className="mt-lg">
                <div className="flex items-end gap-md">
                  <span className="font-display-lg text-display-lg text-primary">{completedCount}</span>
                  <span className="mb-2 px-2 py-0.5 rounded-full bg-secondary-container text-on-secondary-container font-label-caps text-xs">Up 15%!</span>
                </div>
                <p className="font-body-sm text-body-sm text-on-surface-variant mt-1">Since last update</p>
              </div>
            </div>
            {/* Metric 3 */}
            <div className="min-w-[260px] flex-1 bg-surface-container-lowest border border-outline-variant rounded-xl p-md flex flex-col justify-between hover:border-primary transition-colors cursor-default group">
              <div className="flex justify-between items-start">
                <span className="font-label-caps text-label-caps text-on-surface-variant uppercase">Avg. Time Per Task</span>
                <span className="material-symbols-outlined text-on-surface-variant group-hover:text-primary transition-colors" data-icon="timer">timer</span>
              </div>
              <div className="mt-lg">
                <span className="font-display-lg text-display-lg text-primary font-data-tabular">18m 30s</span>
                <div className="flex items-center gap-1 mt-1 text-on-surface-variant">
                  <span className="material-symbols-outlined text-sm" data-icon="trending_down">trending_down</span>
                  <span className="font-body-sm text-body-sm">2m faster than avg</span>
                </div>
              </div>
            </div>
          </section>

          {/* Main Content: Upcoming Tasks */}
          <section className="space-y-md">
            <div className="flex justify-between items-center">
              <h3 className="font-title-md text-title-md text-primary">Upcoming Logistics Tasks</h3>
              <button className="text-secondary font-label-caps text-label-caps hover:underline">View All</button>
            </div>
            <div className="grid grid-cols-1 gap-sm">
              {upcomingTasks.map((task, index) => (
                <div key={task.id} className="bg-surface-container-lowest border border-outline-variant p-md rounded-lg flex items-center justify-between hover:shadow-sm transition-all group">
                  <div className="flex items-center gap-md">
                    <div className="w-12 h-12 rounded bg-surface-container-high flex items-center justify-center">
                      <span className="material-symbols-outlined text-primary" data-icon={index % 2 === 0 ? "unarchive" : "fact_check"}>{index % 2 === 0 ? "unarchive" : "fact_check"}</span>
                    </div>
                    <div>
                      <p className="font-body-lg text-primary font-semibold">{task.name}</p>
                      <p className="font-body-sm text-on-surface-variant">{task.description}</p>
                    </div>
                  </div>
                  <div className="flex flex-col items-end gap-xs">
                    <div className="flex items-center gap-1 text-on-surface-variant">
                      <span className="material-symbols-outlined text-sm" data-icon="schedule">schedule</span>
                      <span className="font-data-tabular text-data-tabular">Est: 45m</span>
                    </div>
                    <span className="bg-surface-container-highest text-on-surface-variant text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-wider">Routine</span>
                  </div>
                </div>
              ))}
            </div>
          </section>
        </main>
      </div>
    );
  }
}