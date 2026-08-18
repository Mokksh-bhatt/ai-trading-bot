import React from 'react';
import Dragula from 'dragula';
import 'dragula/dist/dragula.css';
import Swimlane from './Swimlane';
import './Board.css';

export default class Board extends React.Component {
  constructor(props) {
    super(props);
    
    this.clientsList = []; 
    
    this.state = {
      clients: {
        backlog: [],
        inProgress: [],
        complete: [],
      }
    }
    
    // tracking the column elements for dragula
    this.laneRefs = {
      backlog: React.createRef(),
      inProgress: React.createRef(),
      complete: React.createRef(),
    }
  }
  componentDidMount() {
    // initialize drag and drop
    this.drake = Dragula([
      this.laneRefs.backlog.current,
      this.laneRefs.inProgress.current,
      this.laneRefs.complete.current,
    ]);

    // fetch initial data from backend
    fetch('http://localhost:3001/api/v1/clients')
      .then(res => res.json())
      .then(clients => {
        clients.sort((a, b) => a.priority - b.priority);
        this.clientsList = clients;
        this.setState({
          clients: {
            backlog: clients.filter(t => !t.status || t.status === 'backlog'),
            inProgress: clients.filter(t => t.status === 'in-progress'),
            complete: clients.filter(t => t.status === 'complete'),
          }
        });
      })
      .catch(err => console.error("Error fetching clients", err));

    // what happens when we drop a card
    this.drake.on('drop', (el, target, source, sibling) => {
      // 1. Revert dragula's DOM change
      this.drake.cancel(true);

      // 2. Find the new status
      let newStatus = 'backlog';
      if (target === this.laneRefs.inProgress.current) {
        newStatus = 'in-progress';
      } else if (target === this.laneRefs.complete.current) {
        newStatus = 'complete';
      }
      
      const draggedId = el.getAttribute('data-id');
      const allTasks = [...this.clientsList]; 
      
      // 3. Figure out where to insert it using the sibling to calculate newPriority
      let newPriority = allTasks.filter(t => t.status === newStatus).length + 1; // default to end
      if (sibling) {
        const siblingId = sibling.getAttribute('data-id');
        const siblingTask = allTasks.find(t => String(t.id) === siblingId);
        if (siblingTask) {
          newPriority = siblingTask.priority;
        }
      }
      
      // 4. Send PUT request to backend
      fetch(`http://localhost:3001/api/v1/clients/${draggedId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus, priority: newPriority })
      })
      .then(res => res.json())
      .then(updatedClients => {
        // Ensure they are sorted by priority
        updatedClients.sort((a, b) => a.priority - b.priority);
        this.clientsList = updatedClients;
        this.setState({
          clients: {
            backlog: updatedClients.filter(t => !t.status || t.status === 'backlog'),
            inProgress: updatedClients.filter(t => t.status === 'in-progress'),
            complete: updatedClients.filter(t => t.status === 'complete'),
          }
        });
      })
      .catch(err => console.error("Error updating client", err));
    });
  }
  
  componentWillUnmount() {
    if (this.drake) {
      this.drake.destroy();
    }
  }

  
  // helper to render the columns
  renderSwimlane(name, clients, ref) {
    return (
      <Swimlane name={name} clients={clients} dragulaRef={ref}/>
    );
  }

  render() {
    return (
      <div className="Board">
        <div className="container-fluid">
          <div className="row">
            <div className="col-md-4">
              {this.renderSwimlane('Backlog', this.state.clients.backlog, this.laneRefs.backlog)}
            </div>
            <div className="col-md-4">
              {this.renderSwimlane('In Progress', this.state.clients.inProgress, this.laneRefs.inProgress)}
            </div>
            <div className="col-md-4">
              {this.renderSwimlane('Complete', this.state.clients.complete, this.laneRefs.complete)}
            </div>
          </div>
        </div>
      </div>
    );
  }
}
