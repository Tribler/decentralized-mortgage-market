import { Component, OnInit, Input } from '@angular/core';

@Component({
    selector: 'status',
    template: `
        <span
            class="label label-default"
            [ngClass]="{'label-success': label == 'ACCEPTED', 'label-danger': label == 'REJECTED'}">
            {{ label }}
        </span>
    `
})
export class StatusComponentComponent implements OnInit {
    @Input() label: string;

    constructor() { }

    ngOnInit() {
    }

}
