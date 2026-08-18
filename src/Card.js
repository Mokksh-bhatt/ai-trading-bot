import React from 'react';
import './Card.css';

export default class Card extends React.Component {
  render() {
    let cardClasses = ['Card'];
    
    // push the color class based on status
    if (this.props.status === 'backlog') {
      cardClasses.push('Card-grey');
    } else if (this.props.status === 'in-progress') {
      cardClasses.push('Card-blue');
    } else if (this.props.status === 'complete') {
      cardClasses.push('Card-green');
    }
    
    return (
      <div className={cardClasses.join(' ')} data-id={this.props.id} data-status={this.props.status}>
        <div className="Card-title">{this.props.name}</div>
      </div>
    );
  }
}