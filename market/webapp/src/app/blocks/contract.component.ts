import { Component, OnInit, Input } from '@angular/core';

@Component({
    selector: 'contract',
    templateUrl: 'contract.component.html',
    styleUrls: ['./blocks.component.css']
})
export class ContractComponent implements OnInit {
    @Input() title: string;
    @Input() contract: Object;
    decode = false;

    constructor() { }

    ngOnInit() {
    }
}
